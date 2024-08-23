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


# noinspection PyTypeChecker
class Creator(CreatorSteam, CreatorGeneral, CreatorDataBase, Restarter):
    def __init__(self, tg_info):
        super().__init__(tg_info)

    @staticmethod
    def collect_work_functions(tg_info):

        functions = [
            # Restart Server
            {"func": "restart_server", "class_per_functions": Creator},

            # Restart Bots
            {"func": "restart_bots", "class_per_functions": Creator},

            # Database Prices
            {"func": "database_prices", "class_per_functions": Creator},

            # Database Settings
            {"func": "database_settings", "class_per_functions": Creator},

            # Steam Login
            {"func": "steam_login", "class_name": CreatorSteam},

            # Steam Inventory
            {"func": "steam_inventory", "class_name": CreatorSteam},

            # Steam Access Token
            {"func": "steam_access_token", "class_name": CreatorSteam},

            # Steam Apikey
            {"func": "steam_apikey", "class_name": CreatorSteam},

            # Proxy
            {"func": "proxy", "class_name": CreatorGeneral},

            # MongoDB
            {"func": "mongodb", "class_per_functions": Creator}
        ]

        for function in functions:
            function["tg_info"] = tg_info

        instances = {}
        for function in functions:
            if "class_per_functions" in function:
                class_name = function["class_per_functions"]
                if class_name not in instances:
                    instances[class_name] = class_name(function["tg_info"])
                function["class_per_functions"] = instances[class_name]
            elif "class_name" in function:
                function["class_name"] = function["class_name"](function["tg_info"])
            elif "class_per_functions_and_account" in function:
                function["class_per_functions_and_account"] = function["class_per_functions_and_account"](function["tg_info"])
            else:
                raise

        print(functions)
        return functions


tg_token = '6710866120:AAElhQPr-4PkOnZvvLDSnYA163Ez0td4KzQ'
tg_id = -1001807211917

tg_bot = telebot.TeleBot(tg_token)
main_tg_info = {
    'tg id': tg_id,
    'tg bot': tg_bot,
    'bot name': Logs.get_bot_name()}

Creator.collect_work_functions(main_tg_info)


