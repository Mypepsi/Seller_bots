from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.information.logs import Logs
from bots_libraries.information.mongo import Mongo
from bots_libraries.creator.creator_steam import CreatorSteam
from bots_libraries.creator.creator_database import DataBase
from bots_libraries.information.restart import Restarter
import threading
import time



if __name__ == '__main__':
    try:
        mongo = Mongo()
        database = DataBase()
        restarter = Restarter()
        steam_aut = CreatorSteam()
        steam_api = CreatorSteam()
        steam_inv = CreatorSteam()
        steam_prx = CreatorSteam()
        steam_acs = CreatorSteam()

        Logs.log(f'Creator STARTED')
        # time.sleep(mongo.creator_sleep_before_start)

        # try:
        #     restart_server_schedule_thread = threading.Thread(target=restarter.schedule_restart_server,
        #                                                       args=(restarter.creator_restart_time_sleep,
        #                                                             restarter.creator_restart_server_global_sleep))
        #     restart_server_schedule_thread.start()
        # except Exception as e:
        #     mongo.error_alert('restart_server_schedule_thread', e)


        # try:
        #     if len(mongo.creator_restart_info_bots) != 0:
        #         restart_bots_schedule_thread = threading.Thread(target=restarter.schedule_restart_bots,
        #                                                args=(restarter.creator_restart_info_bots,
        #                                                  restarter.creator_restart_bots_global_sleep))
        #         restart_bots_schedule_thread.start()
        # except Exception as e:
        #     mongo.error_alert('restart_bots_schedule_thread', e)

        try:
            refresh_db_thread = threading.Thread(target=database.refresh_db_thread)
            refresh_db_thread.start()
        except Exception as e:
            mongo.error_alert('refresh_db_thread', e)

        # time.sleep(mongo.creator_sleep_between_threads)
        # try:
        #     refresh_settings_thread = threading.Thread(target=database.refresh_settings_thread)
        #     refresh_settings_thread.start()
        # except Exception as e:
        #     mongo.error_alert('refresh_settings_thread', e)
        #
        # time.sleep(mongo.creator_sleep_between_threads)
        # try:
        #     authorization_thread = threading.Thread(target=steam_aut.work_with_steam_settings,
        #                                             args=(steam_aut.steam_login,
        #                                                   steam_aut.creator_authorization_global_sleep))
        #     authorization_thread.start()
        # except Exception as e:
        #     mongo.error_alert('authorization_thread', e)
        #
        # time.sleep(mongo.creator_sleep_between_threads)
        # try:
        #     steam_inventory_thread = threading.Thread(target=steam_inv.work_with_steam_parsed,
        #                                               args=(steam_inv.steam_inventory,
        #                                                     steam_inv.creator_steam_inventory_global_sleep))
        #     steam_inventory_thread.start()
        # except Exception as e:
        #     mongo.error_alert('steam_inventory_thread', e)
        #
        # time.sleep(mongo.creator_sleep_between_threads)
        # try:
        #     steam_api_key_thread = threading.Thread(target=steam_api.work_with_steam_parsed,
        #                                             args=(steam_api.steam_api_key,
        #                                                   steam_api.creator_steam_api_key_global_sleep))
        #     steam_api_key_thread.start()
        # except Exception as e:
        #     mongo.error_alert('steam_api_key_thread', e)
        #
        # time.sleep(mongo.creator_sleep_between_threads)
        # try:
        #     steam_proxy_checker_thread = threading.Thread(target=steam_prx.work_with_steam_loop,
        #                                                   args=(steam_prx.steam_proxy,
        #                                                         steam_prx.creator_proxy_global_sleep))
        #     steam_proxy_checker_thread.start()
        # except Exception as e:
        #     mongo.error_alert('steam_proxy_checker_thread', e)
        #
        # try:
        #     time.sleep(mongo.creator_access_token_start_sleep)
        #     steam_access_token_thread = threading.Thread(target=steam_acs.work_with_steam_parsed,
        #                                                  args=(steam_acs.steam_access_token,
        #                                                     steam_acs.creator_access_token_global_sleep))
        #     steam_access_token_thread.start()
        # except Exception as e:
        #     mongo.error_alert('steam_access_token_thread', e)

    except ServerSelectionTimeoutError:
        Logs.log("Connecting to MongoDB ERROR")
    except Exception as e:
        Logs.log(f"FATAL ERROR: {e}")





