import time
import telebot
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.buff_seller.items import BuffItems
from bots_libraries.buff_seller.steam import BuffSteam
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.buff_seller.online import BuffOnline
from bots_libraries.buff_seller.general import BuffGeneral
from bots_libraries.buff_seller.history import BuffHistory
from bots_libraries.sellpy.thread_manager import ThreadManager


class BuffSeller(BuffGeneral, BuffOnline, BuffItems, BuffSteam, BuffHistory, Restarter):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    @staticmethod
    def collect_work_functions():
        functions_list = []
        # if manager.update_site_data_global_time != 0:  # Update Site Data
        #     functions_list.append({"func": "update_site_data", "class_for_many_functions": BuffSeller})
        # if manager.update_site_data_global_time != 0:  # Update Site Data
        #     functions_list.append({"func": "site_cookie", "class_for_many_functions": BuffSeller})
        # if manager.update_site_data_global_time != 0:  # Update Site Data
        #     functions_list.append({"func": "balance_transfer", "class_for_many_functions": BuffSeller})

        # if manager.steam_cancel_offers_global_time != 0:  # Steam Cancel Offers
        #     functions_list.append({"func": "steam_cancel_offers", "class_for_account_functions": BuffSeller})

        if manager.history_global_time != 0:  # History
            functions_list.append({"func": "history", "class_for_account_functions": BuffSeller})
        #
        #
        # if manager.restart_server_global_time != 0:  # Restart Server
        #     functions_list.append({"func": "restart_server", "class_for_many_functions": BuffSeller})
        #
        # if manager.restart_bots_global_time != 0:    # Restart Bots
        #     functions_list.append({"func": "restart_bots", "class_for_many_functions": BuffSeller})
        #
        # if manager.ping_global_time != 0:  # Ping
        #     functions_list.append({"func": "ping", "class_for_account_functions": BuffSeller})

        # if manager.visible_store_global_time != 0:  # Visible Store
        #     functions_list.append({"func": "visible_store", "class_for_account_functions": BuffSeller})

        # if manager.add_to_sale_global_time != 0:  # Add To Sale
        #     functions_list.append({"func": "add_to_sale", "class_for_account_functions": BuffSeller})
        #
        # if manager.change_price_global_time != 0:  # Change Price
        #     functions_list.append({"func": "change_price", "class_for_account_functions": BuffSeller})
        #
        if manager.steam_send_offers_global_time != 0:  # Steam Send Offers
            functions_list.append({"func": "steam_send_offers", "class_for_account_functions": BuffSeller})
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
        functions = BuffSeller.collect_work_functions()

        Logs.log(f'{bot_name} STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        # time.sleep(manager.waiting_start_time)
        manager.start_work_functions(functions)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(tg_info, f"Script has not started: FATAL ERROR: {e}", '')
