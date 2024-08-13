import time
import telebot
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam
from bots_libraries.tm_seller.items import TMItems
from bots_libraries.tm_seller.steam import TMSteam
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.tm_seller.online import TMOnline
from bots_libraries.tm_seller.general import TMGeneral
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.tm_seller.history import TMHistory
from bots_libraries.sellpy.thread_manager import ThreadManager


def add_threads(main_tg_info):
    threads_list = []

    if manager.tm_restart_server_global_time != 0:  # Restart Server
        restart_server_thread = threading.Thread(target=restarter.restart_server,
                                                 args=(restarter.tm_tg_info,
                                                       restarter.tm_restart_server_validity_time,
                                                       restarter.tm_restart_server_global_time))
        threads_list.append(restart_server_thread)

    if manager.tm_restart_bots_global_time != 0:  # Restart Bots
        restart_bots_thread = threading.Thread(target=restarter.restart_bots,
                                               args=(restarter.tm_tg_info,
                                                     restarter.tm_restart_bots_name,
                                                     restarter.tm_restart_bots_global_time))
        threads_list.append(restart_bots_thread)

    if manager.tm_steam_cancel_offers_global_time != 0:  # Steam Cancel Offers
        steam_cancel_offers_thread = threading.Thread(target=manager.create_threads,
                                                      args=('_chk_trd',
                                                            Steam(main_tg_info),
                                                            'steam_cancel_offers',
                                                            'tm_steam_cancel_offers_global_time',
                                                            'tm_thread_function_time',
                                                            'tm_tg_info',
                                                            'tm_steam_cancel_offers_sites_name'))
        threads_list.append(steam_cancel_offers_thread)

    if manager.tm_restart_store_global_time != 0:  # Restart Store
        restart_store_thread = threading.Thread(target=manager.create_threads,
                                                args=('_str_png',
                                                      TMOnline(main_tg_info),
                                                      'restart_store',
                                                      'tm_restart_store_global_time',
                                                      'tm_thread_function_time',
                                                      'tm_tg_info'))
        threads_list.append(restart_store_thread)

    if manager.tm_site_apikey_global_time != 0:  # Site Apikey
        site_apikey_thread = threading.Thread(target=api_chk.site_apikey,
                                              args=(api_chk.tm_tg_info,
                                                    api_chk.tm_site_apikey_global_time))
        threads_list.append(site_apikey_thread)

    if manager.tm_ping_global_time != 0:  # Ping
        ping_thread = threading.Thread(target=manager.create_threads,
                                       args=('_onl_thd',
                                             TMOnline(main_tg_info),
                                             'ping',
                                             'tm_ping_global_time',
                                             'tm_thread_function_time',
                                             'tm_tg_info'))
        threads_list.append(ping_thread)

    if manager.tm_steam_send_offers_global_time != 0:  # Steam Send Offers
        steam_send_offers_thread = threading.Thread(target=manager.create_threads,
                                                    args=('_tm_trd',
                                                          TMSteam(main_tg_info),
                                                          'steam_send_offers',
                                                          'tm_steam_send_offers_global_time',
                                                          'tm_thread_function_time',
                                                          'tm_tg_info'))
        threads_list.append(steam_send_offers_thread)

    if manager.tm_add_to_sale_global_time != 0:  # Add To Sale
        add_to_sale_thread = threading.Thread(target=manager.create_threads,
                                              args=('_add_sale',
                                                    TMItems(main_tg_info),
                                                    'add_to_sale',
                                                    'tm_add_to_sale_global_time',
                                                    'tm_thread_function_time',
                                                    'tm_tg_info'))
        threads_list.append(add_to_sale_thread)

    if manager.tm_change_price_global_time != 0:  # Change Price
        change_price_thread = threading.Thread(target=manager.create_threads,
                                               args=('_chg_prc',
                                                     TMItems(main_tg_info),
                                                     'change_price',
                                                     'tm_change_price_global_time',
                                                     'tm_thread_function_time',
                                                     'tm_tg_info'))
        threads_list.append(change_price_thread)

    if manager.tm_balance_transfer_global_time != 0:  # Balance Transfer
        transfer_balance_thread = threading.Thread(target=blc_trf.balance_transfer,
                                                   args=(blc_trf.tm_tg_info,
                                                         blc_trf.tm_balance_transfer_global_time))
        threads_list.append(transfer_balance_thread)

    if manager.tm_history_global_time != 0:  # History
        history_thread = threading.Thread(target=manager.create_threads,
                                          args=('_hstr_thd',
                                                TMHistory(main_tg_info),
                                                'history',
                                                'tm_history_global_time',
                                                'tm_thread_function_time',
                                                'tm_tg_info'))
        threads_list.append(history_thread)

    if manager.tm_visible_store_global_time != 0:  # Visible Store
        visible_store_thread = threading.Thread(target=manager.create_threads,
                                                args=('_str_vsb',
                                                      TMOnline(main_tg_info),
                                                      'visible_store',
                                                      'tm_visible_store_global_time',
                                                      'tm_thread_function_time',
                                                      'tm_tg_info'))
        threads_list.append(visible_store_thread)

    return threads_list


if __name__ == '__main__':
    main_tg_bot = telebot.TeleBot('6710866120:AAElhQPr-4PkOnZvvLDSnYA163Ez0td4KzQ')
    main_tg_info = {
        'tg id': -1001807211917,
        'tg bot': main_tg_bot,
        'bot name': 'TM Seller'}

    try:
        manager = ThreadManager(main_tg_info)
        restarter = Restarter(main_tg_info)
        api_chk = TMGeneral(main_tg_info)
        blc_trf = TMGeneral(main_tg_info)

        threads = add_threads(main_tg_info)

        Logs.log(f'TM Seller STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        time.sleep(manager.tm_waiting_start_time)
        manager.start_of_work(manager.tm_tg_info, threads, manager.tm_thread_start_time)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(main_tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(main_tg_info, f"Script has not started: FATAL ERROR: {e}", '')




