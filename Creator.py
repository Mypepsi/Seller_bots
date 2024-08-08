import time
import telebot
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.creator.database import DataBase
from bots_libraries.creator.steam import CreatorSteam
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.creator.general import CreatorGeneral
from bots_libraries.sellpy.thread_manager import ThreadManager


def add_threads():
    threads_list = []

    if manager.creator_restart_server_global_time != 0:
        restart_server = threading.Thread(target=restarter.restart_server,
                                          args=(restarter.creator_tg_info,
                                                restarter.creator_restart_server_validity_time,
                                                restarter.creator_restart_server_global_time))
        threads_list.append(restart_server)

    if manager.creator_restart_bots_global_time != 0:
        restart_bots = threading.Thread(target=restarter.restart_bots,
                                        args=(restarter.creator_tg_info,
                                              restarter.creator_restart_bots_name,
                                              restarter.creator_restart_bots_global_time))
        threads_list.append(restart_bots)

    if manager.creator_db_prices_global_time != 0:
        database_prices = threading.Thread(target=db_price.database_prices,
                                           args=(db_price.creator_tg_info,
                                                 db_price.creator_db_prices_validity_time,
                                                 db_price.creator_db_prices_global_time))
        threads_list.append(database_prices)

    if manager.creator_db_settings_global_time != 0:
        database_settings = threading.Thread(target=db_settings.database_settings,
                                             args=(db_settings.creator_tg_info,
                                                   db_settings.creator_db_settings_validity_time,
                                                   db_settings.creator_db_settings_global_time))
        threads_list.append(database_settings)

    if manager.creator_steam_session_global_time != 0:
        steam_login = threading.Thread(target=steam_aut.steam_login,
                                       args=(steam_aut.creator_tg_info,
                                             steam_aut.make_steam_login,
                                             steam_aut.creator_steam_session_global_time))
        threads_list.append(steam_login)

    if manager.creator_steam_inventory_global_time != 0:
        steam_inventory = threading.Thread(target=steam_inv.steam_inventory,
                                           args=(steam_inv.creator_tg_info,
                                                 steam_inv.creator_steam_inventory_global_time))
        threads_list.append(steam_inventory)

    if manager.creator_steam_apikey_global_time != 0:
        steam_apikey = threading.Thread(target=steam_api.steam_apikey,
                                         args=(steam_api.creator_tg_info,
                                               steam_api.creator_steam_apikey_global_time))
        threads_list.append(steam_apikey)

    if manager.creator_proxy_global_time != 0:
        proxy_checker = threading.Thread(target=steam_prx.proxy_checker,
                                         args=(steam_prx.creator_tg_info,
                                               steam_prx.creator_proxy_global_time))
        threads_list.append(proxy_checker)

    if manager.creator_steam_access_token_global_time != 0:
        steam_access_token = threading.Thread(target=steam_acs.steam_access_token,
                                              args=(steam_acs.creator_tg_info,
                                                    steam_acs.creator_steam_access_token_global_time,
                                                    False))
        threads_list.append(steam_access_token)

    if manager.creator_mongodb_global_time != 0:
        mongodb_checker = threading.Thread(target=mng_checker.mongodb_checker,
                                           args=(mng_checker.creator_tg_info,
                                                 mng_checker.creator_mongodb_global_time))
        threads_list.append(mongodb_checker)

    return threads_list


if __name__ == '__main__':
    name = 'Creator'
    main_tg_bot = telebot.TeleBot('6710866120:AAElhQPr-4PkOnZvvLDSnYA163Ez0td4KzQ')
    main_tg_info = {
        'tg id': -1001807211917,
        'tg bot': main_tg_bot,
        'bot name': name}

    try:
        manager = ThreadManager(name)
        restarter = Restarter(name)
        db_price = DataBase(name)
        db_settings = DataBase(name)
        steam_aut = CreatorSteam(name)
        steam_inv = CreatorSteam(name)
        steam_api = CreatorSteam(name)
        steam_prx = CreatorGeneral(name)
        steam_acs = CreatorSteam(name)
        mng_checker = CreatorGeneral(name)

        threads = add_threads()
        Logs.log(f'Creator STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        #time.sleep(manager.creator_waiting_start_time)
        manager.start_of_work(manager.creator_tg_info, threads, manager.creator_thread_start_time)


    except ServerSelectionTimeoutError:
        Logs.notify_except(main_tg_info, "Connecting to MongoDB ERROR", '')
    except Exception as e:
        Logs.notify_except(main_tg_info, f"FATAL ERROR: {e}", '')





