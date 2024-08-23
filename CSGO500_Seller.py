import time
import telebot
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam
from bots_libraries.sellpy.restart import Restarter
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.csgo500_seller.items import CSGO500Items
from bots_libraries.csgo500_seller.steam import CSGO500Steam
from bots_libraries.sellpy.thread_manager import ThreadManager
from bots_libraries.csgo500_seller.online import CSGO500Online
from bots_libraries.csgo500_seller.general import CSGO500General
from bots_libraries.csgo500_seller.history import CSGO500History


def add_threads(tg_info):
    threads_list = []

    if manager.csgo500_restart_server_global_time != 0:  # Restart Server
        restart_server_thread = threading.Thread(target=restarter.restart_server,
                                                 args=(restarter.csgo500_restart_server_validity_time,
                                                       restarter.csgo500_restart_server_global_time))
        threads_list.append(restart_server_thread)

    if manager.csgo500_restart_bots_global_time != 0:  # Restart Bots
        restart_bots_thread = threading.Thread(target=restarter.restart_bots,
                                               args=(restarter.csgo500_restart_bots_name,
                                                     restarter.csgo500_restart_bots_global_time))
        threads_list.append(restart_bots_thread)

    if manager.csgo500_steam_cancel_offers_global_time != 0:  # Steam Cancel Offers
        steam_cancel_offers_thread = threading.Thread(target=manager.create_threads,
                                                      args=('_chk_trd',
                                                            Steam(tg_info),
                                                            'steam_cancel_offers',
                                                            'csgo500_steam_cancel_offers_global_time',
                                                            'csgo500_thread_function_time',
                                                            'csgo500_steam_cancel_offers_sites_name'))
        threads_list.append(steam_cancel_offers_thread)



    return threads_list


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
        restarter = Restarter(main_tg_info)

        threads = add_threads(main_tg_info)

        Logs.log(f'{bot_name} STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        time.sleep(manager.waiting_start_time)
        manager.start_of_work(threads, manager.thread_start_time)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(main_tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(main_tg_info, f"Script has not started: FATAL ERROR: {e}", '')




