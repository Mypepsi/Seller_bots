import time

from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.mongo import Mongo
from bots_libraries.base_info.steam import Steam

from bots_libraries.tm_seller.tm_seller_steam import TMSteam
# from bots_libraries.tm_seller.tm_seller_general import TMGeneral
from bots_libraries.tm_seller.tm_seller_online import TMOnline
# from bots_libraries.creator.creator_steam import Steam
# from bots_libraries.creator.creator_database import DataBase
from bots_libraries.base_info.restart import Restarter
import threading
import time


if __name__ == '__main__':
        try:

            mongo = Mongo()
            steam = Steam()
            restarter = Restarter()
            mongo.update_account_data_info()
            # for i in mongo.content_acc_data_list:
            #     username = str(i['username'])
            #     name_func = '_onl_thd'
            #     name = username + name_func
            #     globals()[name] = TMOnline()
            #     thread = threading.Thread(target=globals()[name].ping, args=(i, globals()[name].tm_ping))
            #     thread.start()
            #     time.sleep(globals()[name].tm_thread_function_sleep)



            # for i in mongo.content_acc_data_list:
            #     username = str(i['username'])
            #     name_func = '_str_png'
            #     name = username + name_func
            #     globals()[name] = TMOnline()
            #     thread = threading.Thread(target=globals()[name].store_ping, args=(i, globals()[name].tm_store_ping))
            #     thread.start()
            #     time.sleep(globals()[name].tm_thread_function_sleep)

            # for i in mongo.content_acc_data_list:
            #     username = str(i['username'])
            #     name_func = '_str_png'
            #     name = username + name_func
            #     globals()[name] = TMOnline()
            #     thread = threading.Thread(target=globals()[name].store_items_visible, args=(i, globals()[name].tm_visible_store_global_sleep))
            #     thread.start()
            #     time.sleep(globals()[name].tm_thread_function_sleep)




            steam.create_threads('_onl_thd', 'TMOnline', 'ping', 'tm_thread_function_sleep', 'tm_ping')
            steam.create_threads('_str_png', 'TMOnline', 'store_ping', 'tm_thread_function_sleep', 'tm_store_ping')
            steam.create_threads('_str_vsb', 'TMOnline', 'store_items_visible', 'tm_thread_function_sleep', 'tm_visible_store_global_sleep')
            steam.create_threads('_tm_trd', 'TMSteam', 'tm_trades', 'tm_thread_function_sleep', 'tm_sda_global_sleep')
            steam.create_threads('_add_sale', 'TMSteam', 'add_to_sale', 'tm_thread_function_sleep', 'tm_add_to_sale_global_sleep')
            steam.create_threads('_chg_prc', 'TMSteam', 'change_price', 'tm_thread_function_sleep', 'tm_change_price_global_sleep')
            steam.create_threads('_hstr_thd', 'TMOnline', 'main_history', 'tm_thread_function_sleep', 'tm_history_global_sleep')
            steam.create_threads('_chk_trd', 'TMSteam', 'check_trades_for_cancel', 'tm_thread_function_sleep', 'tm_cancel_offers_global_sleep')


            api_chk = TMOnline()
            blc_trf = TMOnline()

            api_chk.validity_tm_apikey(api_chk.tm_api_key_checker_global_sleep)
            blc_trf.work_with_steam_loop(blc_trf.transfer_balance, blc_trf.tm_transfer_global_sleep)

            # print(1)

            #tm_sda_global_sleep - global sleep for tm_trade
            #tm_add_to_sale_global_sleep - global sleep for add_to_sale




            # наступні три треба адаптувати коли завершим з класом рестартер
            # restart_server_schedule_thread = threading.Thread(target=restarter.schedule_restart_server, args=(restarter.tm_restart_time_sleep, restarter.tm_restart_global_sleep))
            # restart_bots_schedule_thread = threading.Thread(target=restarter.schedule_restart_bots, args=(restarter.tm_restart_info_bots,  restarter.tm_restart_global_sleep))



            # Logs.log(f'TM Seller STARTED')
            # restart_server_schedule_thread.start()
            # restart_bots_schedule_thread.start()
            #


        except ServerSelectionTimeoutError:
           Logs.log("Connecting to MongoDB ERROR")
        except Exception as e:
           Logs.log(f"FATAL ERROR: {e}")




