import time
import telebot
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.creator.steam import CreatorSteam
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.creator.general import CreatorGeneral
from bots_libraries.creator.database import CreatorDataBase
from bots_libraries.sellpy.thread_manager import ThreadManager


class Creator(CreatorGeneral, CreatorDataBase, CreatorSteam, Restarter):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    @staticmethod
    def collect_work_functions():
        functions_list = []
        if manager.db_prices_global_time != 0:  # Database Prices
            functions_list.append({"func": "database_prices", "class_for_many_functions": Creator})

        if manager.db_settings_global_time != 0:  # Database Settings
            functions_list.append({"func": "database_settings", "class_for_many_functions": Creator})

        if manager.steam_login_global_time != 0:  # Steam Login
            functions_list.append({"func": "steam_login", "class_for_single_function": CreatorSteam})

        if manager.steam_inventory_global_time != 0:  # Steam Inventory
            functions_list.append({"func": "steam_inventory", "class_for_single_function": CreatorSteam})

        if manager.steam_apikey_global_time != 0:  # Steam Apikey
            functions_list.append({"func": "steam_apikey", "class_for_single_function": CreatorSteam})

        if manager.proxy_global_time != 0:  # Proxy
            functions_list.append({"func": "proxy", "class_for_single_function": CreatorGeneral})

        if manager.steam_access_token_global_time != 0:  # Steam Access Token
            functions_list.append({"func": "steam_access_token", "class_for_single_function": CreatorSteam})

        if manager.mongodb_global_time != 0:  # MongoDB
            functions_list.append({"func": "mongodb", "class_for_many_functions": Creator})

        if manager.restart_server_global_time != 0:  # Restart Server
            functions_list.append({"func": "restart_server", "class_for_many_functions": Creator})

        if manager.restart_bots_global_time != 0:  # Restart Bots
            functions_list.append({"func": "restart_bots", "class_for_many_functions": Creator})

        return functions_list


if __name__ == '__main__':
    tg_token = '6710866120:AAElhQPr-4PkOnZvvLDSnYA163Ez0td4KzQ'  # Input your Telegram bot token here
    tg_id = -1001807211917  # Input your Telegram chat ID here

    bot_name = Logs.get_bot_name()
    tg_bot = telebot.TeleBot(tg_token)
    tg_info = {
        'tg id': tg_id,
        'tg bot': tg_bot,
        'bot name': bot_name}

    try:
        manager = ThreadManager(tg_info)
        functions = Creator.collect_work_functions()

        Logs.log(f'{bot_name} STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        # time.sleep(manager.waiting_start_time)
        manager.start_work_functions(functions)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(tg_info, f"Script has not started: FATAL ERROR: {e}", '')
