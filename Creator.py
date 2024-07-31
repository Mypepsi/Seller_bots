import time
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.creator.database import DataBase
from bots_libraries.creator.steam import CreatorSteam
from bots_libraries.creator.general import CreatorGeneral
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.sellpy.thread_manager import ThreadManager


def add_threads():
    thread_list = []

    # restart_server_thread = threading.Thread(target=restarter.restart_server,
    #                                                   args=(restarter.creator_restart_time_sleep,
    #                                                         restarter.creator_restart_server_global_sleep))
    # thread_list.append(restart_server_thread)
    #
    # if len(manager.creator_restart_info_bots) != 0:
    #     restart_bots_thread = threading.Thread(target=restarter.restart_bots,
    #                                                     args=(restarter.creator_restart_info_bots,
    #                                                           restarter.creator_restart_bots_global_sleep))
    #     thread_list.append(restart_bots_thread)
    #
    # refresh_db_thread = threading.Thread(target=database.refresh_db_thread)
    # thread_list.append(refresh_db_thread)
    #
    refresh_settings_thread = threading.Thread(target=database.refresh_settings_thread)
    thread_list.append(refresh_settings_thread)
    #
    # authorization_thread = threading.Thread(target=steam_aut.steam_login,
    #                                         args=(steam_aut.make_steam_login,
    #                                               steam_aut.creator_authorization_global_sleep))
    # thread_list.append(authorization_thread)
    #
    # steam_inventory_thread = threading.Thread(target=steam_inv.create_threads_with_acc_data,
    #                                           args=(steam_inv.steam_inventory,
    #                                                 steam_inv.creator_steam_inventory_global_sleep))
    # thread_list.append(steam_inventory_thread)
    #
    # steam_api_key_thread = threading.Thread(target=steam_api.create_threads_with_acc_data,
    #                                         args=(steam_api.steam_api_key,
    #                                               steam_api.creator_steam_api_key_global_sleep))
    # thread_list.append(steam_api_key_thread)
    #
    # steam_proxy_checker_thread = threading.Thread(target=steam_prx.create_threads_with_loop,
    #                                               args=(steam_prx.proxy_checker,
    #                                                     steam_prx.creator_proxy_global_sleep))
    # thread_list.append(steam_proxy_checker_thread)
    #
    # steam_access_token_thread = threading.Thread(target=steam_acs.create_threads_with_acc_data,
    #                                              args=(steam_acs.steam_access_token,
    #                                                    steam_acs.creator_access_token_global_sleep, False))
    # thread_list.append(steam_access_token_thread)
    return thread_list


if __name__ == '__main__':
    try:
        manager = ThreadManager()
        database = DataBase()
        restarter = Restarter()
        steam_aut = CreatorSteam()
        steam_api = CreatorSteam()
        steam_inv = CreatorSteam()
        steam_prx = CreatorGeneral()
        steam_acs = CreatorSteam()

        threads = add_threads()
        Logs.log(f'Creator STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_list)} in Account Settings)')
        #time.sleep(manager.creator_sleep_before_start)
        manager.start_of_work(manager.creator_tg_info, threads, manager.creator_sleep_between_threads)


    except ServerSelectionTimeoutError:
        Logs.log("Connecting to MongoDB ERROR")
    except Exception as e:
        Logs.log(f"FATAL ERROR: {e}")





