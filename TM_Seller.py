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
    while True:
        #try:
            mongo = Mongo()
            onl_thrds = TMOnline()
            print(1)
            onl_thrds.work_with_steam_create_thread(onl_thrds.online, onl_thrds.tm_thread_function_sleep)
            # і так даліекземпляри класів

            print(2)
            #authorization_thread = threading.Thread(target=steam_aut.work_with_steam_settings,
            #                                        args=(steam_aut.steam_login, steam_aut.authorization_global_sleep))
            # і так далі присвоєння тредів


            # Library.check_and_install_libraries()
            # Logs.log(f'Creator STARTED')
            #refresh_settings_thread.start() і так далі запуск тредів
            #time.sleep(mongo.tm_sleep_before_start)
            # рестарт сервера
            # рестарт бота
            time.sleep(mongo.tm_sleep_between_threads)
            time.sleep(mongo.tm_sleep_between_threads)
            time.sleep(mongo.tm_sleep_between_threads)
            time.sleep(mongo.tm_sleep_between_threads)


            #refresh_db_thread.join() і так далі по join тредам


        #except ServerSelectionTimeoutError:
        #    Logs.log("Connecting to MongoDB ERROR")
        #except Exception as e:
        #    Logs.log(f"FATAL ERROR: {e}")

        #time.sleep(300)



