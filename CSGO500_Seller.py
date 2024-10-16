import time
import telebot
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.restart import Restarter
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.csgo500_seller.items import CSGO500Items
from bots_libraries.csgo500_seller.steam import CSGO500Steam
from bots_libraries.sellpy.thread_manager import ThreadManager
from bots_libraries.csgo500_seller.online import CSGO500Online
from bots_libraries.csgo500_seller.general import CSGO500General
from bots_libraries.csgo500_seller.history import CSGO500History


class CSGO500Seller(CSGO500General, CSGO500Online, CSGO500Items, CSGO500Steam, CSGO500History, Restarter):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    @staticmethod
    def collect_work_functions():
        functions_list = []
        # if manager.db_csgo500_global_time != 0:  # Database CSGO500
        #     functions_list.append({"func": "database_csgo500", "class_for_account_functions": CSGO500Seller})

        if manager.update_site_data_global_time != 0:  # Update Site Data
            functions_list.append({"func": "update_site_data", "class_for_many_functions": CSGO500Seller})

        # if manager.steam_cancel_offers_global_time != 0:  # Steam Cancel Offers
        #     functions_list.append({"func": "steam_cancel_offers", "class_for_account_functions": CSGO500Seller})

        # if manager.history_global_time != 0:  # History
        #     functions_list.append({"func": "history", "class_for_account_functions": CSGO500Seller})
        #
        #
        # if manager.restart_server_global_time != 0:  # Restart Server
        #     functions_list.append({"func": "restart_server", "class_for_many_functions": CSGO500Seller})
        #
        # if manager.restart_bots_global_time != 0:    # Restart Bots
        #     functions_list.append({"func": "restart_bots", "class_for_many_functions": CSGO500Seller})
        #
        # if manager.ping_global_time != 0:  # Ping
        #     functions_list.append({"func": "ping", "class_for_account_functions": CSGO500Seller})

        # if manager.visible_store_global_time != 0:  # Visible Store
        #     functions_list.append({"func": "visible_store", "class_for_account_functions": CSGO500Seller})
        #
        # if manager.add_to_sale_global_time != 0:  # Add To Sale
        #     functions_list.append({"func": "add_to_sale", "class_for_account_functions": CSGO500Seller})
        #
        # if manager.change_price_global_time != 0:  # Change Price
        #     functions_list.append({"func": "change_price", "class_for_account_functions": CSGO500Seller})
        #
        # if manager.steam_send_offers_global_time != 0:  # Steam Send Offers
        #     functions_list.append({"func": "steam_send_offers", "class_for_account_functions": CSGO500Seller})
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
        functions = CSGO500Seller.collect_work_functions()

        Logs.log(f'{bot_name} STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        # time.sleep(manager.waiting_start_time)
        manager.start_work_functions(functions)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(tg_info, f"Script has not started: FATAL ERROR: {e}", '')
