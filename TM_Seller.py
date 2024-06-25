from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.mongo import Mongo
from bots_libraries.tm_seller.tm_seller_steam import TMSteam
# from bots_libraries.tm_seller.tm_seller_general import TMGeneral
from bots_libraries.tm_seller.tm_seller_online import TMOnline
# from bots_libraries.creator.creator_steam import Steam
# from bots_libraries.creator.creator_database import DataBase
from bots_libraries.base_info.restart import Restarter
# import threading
# import time


if __name__ == '__main__':
        try:
            mongo = Mongo()
            restarter = Restarter()
            onl_thd = TMOnline()
            str_png = TMOnline()
            str_vsb = TMOnline()
            api_chk = TMOnline()
            add_sale = TMSteam()
            tm_trd = TMSteam()


            # onl_thd.work_with_steam_create_thread(onl_thd.ping, onl_thd.tm_ping, onl_thd.tm_thread_function_sleep)
            # str_png.work_with_steam_create_thread(str_png.store_ping, str_png.tm_store_ping, onl_thd.tm_thread_function_sleep)
            # str_vsb.work_with_steam_create_thread(str_vsb.store_items_visible, str_vsb.tm_visible_store_global_sleep, str_vsb.tm_thread_function_sleep)
            # api_chk.validity_tm_apikey(api_chk.tm_api_key_checker_global_sleep)
            #add_sale.work_with_steam_create_thread(add_sale.add_to_sale, add_sale.tm_add_to_sale_global_sleep, add_sale.tm_thread_function_sleep)

            print(1)
            tm_trd.work_with_steam_create_thread(tm_trd.tm_trades, tm_trd.tm_sda_global_sleep, tm_trd.tm_thread_function_sleep)

            print(2)
            #tm_sda_global_sleep - global sleep for tm_trade
            #tm_add_to_sale_global_sleep - global sleep for add_to_sale

            print(2)
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




