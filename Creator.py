import time
import telebot
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.creator.steam import CreatorSteam
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.creator.general import CreatorGeneral
from bots_libraries.creator.database import CreatorDataBase
from bots_libraries.sellpy.thread_manager import ThreadManager


class Creator(CreatorSteam, CreatorGeneral, CreatorDataBase, Restarter):
    def __init__(self, tg_info):
        super().__init__(tg_info)

    @staticmethod
    def collect_work_functions(tg_info):
        functions_list = []
        if manager.restart_server_global_time != 0:  # Restart Server
            functions_list.append({"func": "restart_server", "class_per_functions": Creator})

        if manager.restart_bots_global_time != 0:  # Restart Bots
            functions_list.append({"func": "restart_bots", "class_per_functions": Creator})

        if manager.db_prices_global_time != 0:  # Database Prices
            functions_list.append({"func": "database_prices", "class_per_functions": Creator})

        if manager.db_settings_global_time != 0:  # Database Settings
            functions_list.append({"func": "database_settings", "class_per_functions": Creator})

        if manager.steam_session_global_time != 0:  # Steam Login
            functions_list.append({"func": "steam_login", "class_name": CreatorSteam})

        if manager.steam_inventory_global_time != 0:  # Steam Inventory
            functions_list.append({"func": "steam_inventory", "class_name": CreatorSteam})

        if manager.steam_access_token_global_time != 0:  # Steam Access Token
            functions_list.append({"func": "steam_access_token", "class_name": CreatorSteam})

        if manager.steam_apikey_global_time != 0:  # Steam Apikey
            functions_list.append({"func": "steam_apikey", "class_name": CreatorSteam})

        if manager.proxy_global_time != 0:  # Proxy
            functions_list.append({"func": "proxy", "class_name": CreatorGeneral})

        if manager.mongodb_global_time != 0:  # Mongodb Checker
            functions_list.append({"func": "mongodb", "class_per_functions": Creator})

        for function in functions_list:
            function["tg_info"] = tg_info

        return functions_list


if __name__ == '__main__':
    tg_token = '6710866120:AAElhQPr-4PkOnZvvLDSnYA163Ez0td4KzQ'
    tg_id = -1001807211917
    bot_name = Logs.get_bot_name()
    tg_bot = telebot.TeleBot(tg_token)
    main_tg_info = {
        'tg id': tg_id,
        'tg bot': tg_bot,
        'bot name': bot_name}

    try:
        manager = ThreadManager(main_tg_info)
        functions = Creator.collect_work_functions(main_tg_info)

        Logs.log(f'{bot_name} STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        # time.sleep(manager.waiting_start_time)
        manager.start_of_work(functions)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(main_tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(main_tg_info, f"Script has not started: FATAL ERROR: {e}", '')





