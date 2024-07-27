from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.thread_manager import ThreadManager
from bots_libraries.tm_seller.online import TMOnline
from bots_libraries.tm_seller.steam import TMSteam
from bots_libraries.tm_seller.general import TMGeneral
from bots_libraries.tm_seller.items import TMItems
from bots_libraries.tm_seller.history import TMHistory
from bots_libraries.base_info.restart import Restarter
import threading
import time


def add_threads():
    thread_list = []

    # restart_server_schedule_thread = threading.Thread(target=restarter.schedule_restart_server,
    #                                                   args=(restarter.tm_restart_time_sleep,
    #                                                         restarter.tm_restart_server_global_sleep))
    # thread_list.append(restart_server_schedule_thread)
    #
    # restart_bots_schedule_thread = threading.Thread(target=restarter.schedule_restart_bots,
    #                                                 args=(restarter.tm_restart_info_bots,
    #                                                       restarter.tm_restart_bots_global_sleep))
    # thread_list.append(restart_bots_schedule_thread)
    #
    # restart_site_store_thread = threading.Thread(target=manager.create_threads,
    #                                              args=('_str_png', TMOnline(), 'restart_site_store',
    #                                                    'tm_restart_store_global_sleep', 'tm_thread_function_sleep'))
    # thread_list.append(restart_site_store_thread)
    #
    # validity_apikey_thread = threading.Thread(target=api_chk.create_threads_with_loop,
    #                                           args=(api_chk.validity_tm_apikey,
    #                                                 api_chk.tm_api_key_checker_global_sleep))
    # thread_list.append(validity_apikey_thread)
    #
    # online_thread = threading.Thread(target=manager.create_threads,
    #                                  args=('_onl_thd', TMOnline(), 'ping', 'tm_ping_global_sleep',
    #                                        'tm_thread_function_sleep'))
    # thread_list.append(online_thread)
    #
    # trades_thread = threading.Thread(target=manager.create_threads,
    #                                  args=('_tm_trd', TMSteam(), 'steam_send_offers', 'tm_sda_global_sleep',
    #                                        'tm_thread_function_sleep'))
    # thread_list.append(trades_thread)
    #
    steam_cancel_offers_thread = threading.Thread(target=manager.create_threads,
                                                      args=('_chk_trd', TMSteam(), 'steam_cancel_offers',
                                                            'tm_cancel_offers_global_sleep',
                                                            'tm_thread_function_sleep', 'tm_cancel_offers_sites_name'))
    thread_list.append(steam_cancel_offers_thread)

    #
    # add_to_sale_thread = threading.Thread(target=manager.create_threads,
    #                                       args=('_add_sale', TMItems(), 'add_to_sale', 'tm_add_to_sale_global_sleep',
    #                                             'tm_thread_function_sleep'))
    # thread_list.append(add_to_sale_thread)
    #
    # change_price_thread = threading.Thread(target=manager.create_threads,
    #                                        args=('_chg_prc', TMItems(), 'change_price',
    #                                              'tm_change_price_global_sleep', 'tm_thread_function_sleep'))
    # thread_list.append(change_price_thread)
    #
    # transfer_balance_thread = threading.Thread(target=blc_trf.create_threads_with_loop,
    #                                            args=(blc_trf.transfer_balance, blc_trf.tm_transfer_global_sleep))
    # thread_list.append(transfer_balance_thread)
    #
    # history_thread = threading.Thread(target=manager.create_threads,
    #                                   args=('_hstr_thd', TMHistory(), 'history_check', 'tm_history_global_sleep',
    #                                         'tm_thread_function_sleep'))
    # thread_list.append(history_thread)
    #
    # store_items_visible_thread = threading.Thread(target=manager.create_threads,
    #                                               args=('_str_vsb', TMOnline(), 'store_items_visible',
    #                                                     'tm_visible_store_global_sleep', 'tm_thread_function_sleep'))
    # thread_list.append(store_items_visible_thread)

    return thread_list



if __name__ == '__main__':
        try:
            manager = ThreadManager()
            restarter = Restarter()
            api_chk = TMGeneral()
            blc_trf = TMGeneral()

            threads = add_threads()

            Logs.log(f'TM Seller STARTED ({len(manager.content_acc_data_list)} in Account Data '
                     f'and {len(manager.content_acc_list)} in Account Settings)')
            #time.sleep(manager.tm_sleep_before_start)
            manager.start_of_work(manager.tm_tg_info, threads, manager.tm_sleep_between_threads)

        except ServerSelectionTimeoutError:
           Logs.log("Connecting to MongoDB ERROR")
        except Exception as e:
           Logs.log(f"FATAL ERROR: {e}")




