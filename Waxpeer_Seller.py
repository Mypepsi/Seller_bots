import time
import telebot
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.restart import Restarter
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.waxpeer_seller.items import WaxpeerItems
from bots_libraries.waxpeer_seller.steam import WaxpeerSteam
from bots_libraries.sellpy.thread_manager import ThreadManager
from bots_libraries.waxpeer_seller.online import WaxpeerOnline
from bots_libraries.waxpeer_seller.general import WaxpeerGeneral
from bots_libraries.waxpeer_seller.history import WaxpeerHistory


class WaxpeerSeller(WaxpeerGeneral, WaxpeerOnline, WaxpeerItems, WaxpeerSteam, WaxpeerHistory, Restarter):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    @staticmethod
    def collect_work_functions():
        functions_list = []
        if manager.steam_cancel_offers_global_time != 0:  # Steam Cancel Offers
            functions_list.append({"func": "steam_cancel_offers", "class_for_account_functions": WaxpeerSeller})

        if manager.restart_server_global_time != 0:  # Restart Server
            functions_list.append({"func": "restart_server", "class_for_many_functions": WaxpeerSeller})

        if manager.restart_bots_global_time != 0:    # Restart Bots
            functions_list.append({"func": "restart_bots", "class_for_many_functions": WaxpeerSeller})

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
        functions = WaxpeerSeller.collect_work_functions()

        Logs.log(f'{bot_name} STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        time.sleep(manager.waiting_start_time)
        manager.start_work_functions(functions)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(tg_info, f"Script has not started: FATAL ERROR: {e}", '')
