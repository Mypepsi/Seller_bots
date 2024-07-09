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

            steam.create_threads('_onl_thd', 'TMOnline', 'ping', 'tm_ping_global_sleep', 'tm_thread_function_sleep')
            steam.create_threads('_str_png', 'TMOnline', 'store_ping', 'tm_store_ping_global_sleep', 'tm_thread_function_sleep')
            steam.create_threads('_str_vsb', 'TMOnline', 'store_items_visible', 'tm_visible_store_global_sleep', 'tm_thread_function_sleep')
            steam.create_threads('_hstr_thd', 'TMOnline', 'main_history', 'tm_history_global_sleep', 'tm_thread_function_sleep')
            steam.create_threads('_tm_trd', 'TMSteam', 'tm_trades', 'tm_sda_global_sleep', 'tm_thread_function_sleep')
            steam.create_threads('_add_sale', 'TMSteam', 'add_to_sale', 'tm_add_to_sale_global_sleep', 'tm_thread_function_sleep')
            steam.create_threads('_chg_prc', 'TMSteam', 'change_price', 'tm_change_price_global_sleep', 'tm_thread_function_sleep')
            steam.create_threads('_chk_trd', 'TMSteam', 'check_trades_for_cancel', 'tm_cancel_offers_global_sleep', 'tm_thread_function_sleep')


            api_chk = TMOnline()
            blc_trf = TMOnline()

            api_chk.validity_tm_apikey(api_chk.tm_api_key_checker_global_sleep)
            blc_trf.work_with_steam_loop(blc_trf.transfer_balance, blc_trf.tm_transfer_global_sleep)

            # print(1)





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




