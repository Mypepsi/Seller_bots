from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.information.logs import Logs
from bots_libraries.information.mongo import Mongo
from bots_libraries.tm_seller.tm_seller_steam import TMSteam
from bots_libraries.tm_seller.tm_seller_general import TMGeneral
from bots_libraries.tm_seller.tm_seller_online import TMOnline
from bots_libraries.creator.creator_steam import Steam
from bots_libraries.creator.creator_database import DataBase
from bots_libraries.information.restart import Restarter
import threading
import time


if __name__ == '__main__':
        try:
            mongo = Mongo()
            restarter = Restarter()
            onl_thd = TMOnline()
            str_png = TMOnline()

            print(1)
            onl_thd.work_with_steam_create_thread(onl_thd.ping, onl_thd.tm_ping,
                                                  onl_thd.tm_thread_function_sleep)  #shouldn't be a thread
            str_png.work_with_steam_create_thread(str_png.store_ping, str_png.tm_store_ping,
                                                  onl_thd.tm_thread_function_sleep)  #shouldn't be a thread
            print(2)
            # restart_server_schedule_thread = threading.Thread(target=restarter.schedule_restart_server,
            #                                                   args=(restarter.tm_restart_time_sleep,
            #                                                         restarter.tm_restart_global_sleep))
            # restart_bots_schedule_thread = threading.Thread(target=restarter.schedule_restart_bots,
            #                                                 args=(restarter.tm_restart_info_bots,
            #                                                       restarter.tm_restart_global_sleep))



            # Logs.log(f'TM Seller STARTED')
            # restart_server_schedule_thread.start()
            # restart_bots_schedule_thread.start()
            #


        except ServerSelectionTimeoutError:
           Logs.log("Connecting to MongoDB ERROR")
        except Exception as e:
           Logs.log(f"FATAL ERROR: {e}")




