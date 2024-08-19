import time
import telebot
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.buff_seller.items import BuffItems
from bots_libraries.buff_seller.steam import BuffSteam
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.buff_seller.online import BuffOnline
from bots_libraries.buff_seller.general import BuffGeneral
from bots_libraries.buff_seller.history import BuffHistory
from bots_libraries.sellpy.thread_manager import ThreadManager


def add_threads(tg_info):
    threads_list = []

    if manager.buff_restart_server_global_time != 0:  # Restart Server
        restart_server_thread = threading.Thread(target=restarter.restart_server,
                                                 args=(restarter.buff_restart_server_validity_time,
                                                       restarter.buff_restart_server_global_time))
        threads_list.append(restart_server_thread)

    if manager.buff_restart_bots_global_time != 0:  # Restart Bots
        restart_bots_thread = threading.Thread(target=restarter.restart_bots,
                                               args=(restarter.buff_restart_bots_name,
                                                     restarter.buff_restart_bots_global_time))
        threads_list.append(restart_bots_thread)

    if manager.buff_steam_cancel_offers_global_time != 0:  # Steam Cancel Offers
        steam_cancel_offers_thread = threading.Thread(target=manager.create_threads,
                                                      args=('_chk_trd',
                                                            Steam(tg_info),
                                                            'steam_cancel_offers',
                                                            'buff_steam_cancel_offers_global_time',
                                                            'buff_thread_function_time',
                                                            'buff_steam_cancel_offers_sites_name'))
        threads_list.append(steam_cancel_offers_thread)



    return threads_list


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
        restarter = Restarter(main_tg_info)

        threads = add_threads(main_tg_info)

        Logs.log(f'{main_tg_info["bot name"]} STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        time.sleep(manager.buff_waiting_start_time)
        manager.start_of_work(threads, manager.buff_thread_start_time)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(main_tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(main_tg_info, f"Script has not started: FATAL ERROR: {e}", '')




