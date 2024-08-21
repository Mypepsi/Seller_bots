import time
import telebot
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam
from bots_libraries.tm_seller.items import TMItems
from bots_libraries.tm_seller.steam import TMSteam
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.tm_seller.online import TMOnline
from bots_libraries.tm_seller.general import TMGeneral
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.tm_seller.history import TMHistory
from bots_libraries.sellpy.thread_manager import ThreadManager


class TMSeller(TMGeneral, TMOnline, TMItems, TMSteam, TMHistory, Restarter):
    def __init__(self, tg_info):
        super().__init__(tg_info)

    @staticmethod
    def collect_work_functions(tg_info):
        functions_info = []
        if manager.tm_restart_server_global_time != 0:  # Restart Server
            functions_info.append({"func": "restart_server", "class_per_functions": TMSeller})

        if manager.tm_restart_bots_global_time != 0:    # Restart Bots
            functions_info.append({"func": "restart_bots", "class_per_functions": TMSeller})

        if manager.tm_steam_cancel_offers_global_time != 0:  # Steam Cancel Offers
            functions_info.append({"func": "steam_cancel_offers", "class_per_functions_and_account": TMSeller})

        if manager.tm_restart_store_global_time != 0:  # Restart Store
            functions_info.append({"func": "restart_store", "class_per_functions_and_account": TMSeller})

        if manager.tm_site_apikey_global_time != 0:  # Site Apikey
            functions_info.append({"func": "site_apikey", "class_per_functions": TMSeller})

        if manager.tm_ping_global_time != 0:  # Ping
            functions_info.append({"func": "ping", "class_per_functions_and_account": TMSeller})

        if manager.tm_steam_send_offers_global_time != 0:  # Steam Send Offers
            functions_info.append({"func": "steam_send_offers", "class_per_functions_and_account": TMSeller})

        if manager.tm_add_to_sale_global_time != 0:  # Add To Sale
            functions_info.append({"func": "add_to_sale", "class_per_functions_and_account": TMSeller})

        if manager.tm_change_price_global_time != 0:  # Change Price
            functions_info.append({"func": "change_price", "class_per_functions_and_account": TMSeller})

        if manager.tm_balance_transfer_global_time != 0:  # Balance Transfer
            functions_info.append({"func": "balance_transfer", "class_per_functions": TMSeller})

        if manager.tm_history_global_time != 0:  # History
            functions_info.append({"func": "history", "class_per_functions_and_account": TMSeller})

        if manager.tm_visible_store_global_time != 0:  # Visible Store
            functions_info.append({"func": "visible_store", "class_per_functions_and_account": TMSeller})

        for funk in functions_info:
            funk["tg_info"] = tg_info

        return functions_info


if __name__ == '__main__':
    tg_token = '6710866120:AAElhQPr-4PkOnZvvLDSnYA163Ez0td4KzQ'
    tg_id = -1001807211917

    main_tg_bot = telebot.TeleBot(tg_token)
    main_tg_info = {
        'tg id': tg_id,
        'tg bot': main_tg_bot,
        'bot name': Logs.get_bot_name()}

    try:
        manager = ThreadManager(main_tg_info)

        threads = TMSeller.collect_work_functions(main_tg_info)

        Logs.log(f'{main_tg_info["bot name"]} STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        #time.sleep(manager.tm_waiting_start_time)
        manager.start_of_work(threads)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(main_tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(main_tg_info, f"Script has not started: FATAL ERROR: {e}", '')




