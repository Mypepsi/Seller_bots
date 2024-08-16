import time
import telebot
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.creator.database import CreatorDataBase
from bots_libraries.creator.steam import CreatorSteam
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.creator.general import CreatorGeneral
from bots_libraries.sellpy.thread_manager import ThreadManager


def add_threads():
    threads_list = []

    if manager.creator_restart_server_global_time != 0:  # Restart Server
        restart_server_thread = threading.Thread(target=restarter.restart_server,
                                                 args=(restarter.creator_tg_info,
                                                       restarter.creator_restart_server_validity_time,
                                                       restarter.creator_restart_server_global_time))
        threads_list.append(restart_server_thread)

    if manager.creator_restart_bots_global_time != 0:  # Restart Bots
        restart_bots_thread = threading.Thread(target=restarter.restart_bots,
                                               args=(restarter.creator_tg_info,
                                                     restarter.creator_restart_bots_name,
                                                     restarter.creator_restart_bots_global_time))
        threads_list.append(restart_bots_thread)

    if manager.creator_db_prices_global_time != 0:  # Database Prices
        database_prices_thread = threading.Thread(target=db_price.database_prices,
                                                  args=(db_price.creator_tg_info,
                                                        db_price.creator_db_prices_validity_time,
                                                        db_price.creator_db_prices_global_time))
        threads_list.append(database_prices_thread)

    if manager.creator_db_settings_global_time != 0:  # Database Settings
        database_settings_thread = threading.Thread(target=db_settings.database_settings,
                                                    args=(db_settings.creator_tg_info,
                                                          db_settings.creator_db_settings_validity_time,
                                                          db_settings.creator_db_settings_global_time))
        threads_list.append(database_settings_thread)

    if manager.creator_steam_session_global_time != 0:  # Steam Login
        steam_login_thread = threading.Thread(target=steam_aut.steam_login,
                                              args=(steam_aut.creator_tg_info,
                                                    steam_aut.creator_steam_session_global_time))
        threads_list.append(steam_login_thread)

    if manager.creator_steam_inventory_global_time != 0:  # Steam Inventory
        steam_inventory_thread = threading.Thread(target=steam_inv.steam_inventory,
                                                  args=(steam_inv.creator_tg_info,
                                                        steam_inv.creator_steam_inventory_global_time))
        threads_list.append(steam_inventory_thread)

    if manager.creator_steam_apikey_global_time != 0:  # Steam Apikey
        steam_apikey_thread = threading.Thread(target=steam_api.steam_apikey,
                                               args=(steam_api.creator_tg_info,
                                                     steam_api.creator_steam_apikey_global_time))
        threads_list.append(steam_apikey_thread)

    if manager.creator_proxy_global_time != 0:  # Proxy Checker
        proxy_checker_thread = threading.Thread(target=steam_prx.proxy_checker,
                                                args=(steam_prx.creator_tg_info,
                                                      steam_prx.creator_proxy_global_time))
        threads_list.append(proxy_checker_thread)

    if manager.creator_steam_access_token_global_time != 0:  # Steam Access Token
        steam_access_token_thread = threading.Thread(target=steam_acs.steam_access_token,
                                                     args=(steam_acs.creator_tg_info,
                                                           steam_acs.creator_steam_access_token_global_time))
        threads_list.append(steam_access_token_thread)

    if manager.creator_mongodb_global_time != 0:  # Mongodb Checker
        mongodb_checker_thread = threading.Thread(target=mng_checker.mongodb_checker,
                                                  args=(mng_checker.creator_tg_info,
                                                        mng_checker.creator_mongodb_global_time))
        threads_list.append(mongodb_checker_thread)

    return threads_list


if __name__ == '__main__':
    main_tg_bot = telebot.TeleBot('6710866120:AAElhQPr-4PkOnZvvLDSnYA163Ez0td4KzQ')
    main_tg_info = {
        'tg id': -1001807211917,
        'tg bot': main_tg_bot,
        'bot name': 'Creator'}

    try:
        manager = ThreadManager(main_tg_info)
        restarter = Restarter(main_tg_info)
        db_price = CreatorDataBase(main_tg_info)
        db_settings = CreatorDataBase(main_tg_info)
        steam_aut = CreatorSteam(main_tg_info)
        steam_inv = CreatorSteam(main_tg_info)
        steam_api = CreatorSteam(main_tg_info)
        steam_prx = CreatorGeneral(main_tg_info)
        steam_acs = CreatorSteam(main_tg_info)
        mng_checker = CreatorGeneral(main_tg_info)

        threads = add_threads()

        Logs.log(f'Creator STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        time.sleep(manager.creator_waiting_start_time)
        manager.start_of_work(manager.creator_tg_info, threads, manager.creator_thread_start_time)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(main_tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(main_tg_info, f"Script has not started: FATAL ERROR: {e}", '')





