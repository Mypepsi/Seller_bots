from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.information.logs import Logs
from bots_libraries.information.mongo import Mongo
from bots_libraries.creator.creator_steam import CreatorSteam
from bots_libraries.creator.creator_database import DataBase
from bots_libraries.information.restart import Restarter
import threading
import time


if __name__ == '__main__':
    while True:
        try:
            mongo = Mongo()
            database = DataBase()
            restarter = Restarter()
            steam_aut = CreatorSteam()
            steam_api = CreatorSteam()
            steam_inv = CreatorSteam()
            steam_prx = CreatorSteam()
            steam_acstn = CreatorSteam()

            steam_api_key_thread = threading.Thread(target=steam_api.work_with_steam_parsed,
                                                    args=(steam_api.steam_api_key, steam_api.creator_steam_api_key_global_sleep))

            steam_api_key_thread.start()

            time.sleep(mongo.creator_access_token_start_sleep)
            steam_api_key_thread.join()

        except ServerSelectionTimeoutError:
            Logs.log("Connecting to MongoDB ERROR")
        except Exception as e:
            Logs.log(f"FATAL ERROR: {e}")

        time.sleep(300)



