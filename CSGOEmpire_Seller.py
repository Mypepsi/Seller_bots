import time
import telebot
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam
from bots_libraries.csgoempire_seller.items import CSGOEmpireItems
from bots_libraries.csgoempire_seller.steam import CSGOEmpireSteam
from bots_libraries.sellpy.restart import Restarter
from bots_libraries.csgoempire_seller.online import CSGOEmpireOnline
from bots_libraries.csgoempire_seller.general import CSGOEmpireGeneral
from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.csgoempire_seller.history import CSGOEmpireHistory
from bots_libraries.sellpy.thread_manager import ThreadManager


def add_threads(main_tg_info):
    threads_list = []

    if manager.csgoempire_restart_server_global_time != 0:  # Restart Server
        restart_server_thread = threading.Thread(target=restarter.restart_server,
                                                 args=(restarter.csgoempire_tg_info,
                                                       restarter.csgoempire_restart_server_validity_time,
                                                       restarter.csgoempire_restart_server_global_time))
        threads_list.append(restart_server_thread)

    if manager.csgoempire_restart_bots_global_time != 0:  # Restart Bots
        restart_bots_thread = threading.Thread(target=restarter.restart_bots,
                                               args=(restarter.csgoempire_tg_info,
                                                     restarter.csgoempire_restart_bots_name,
                                                     restarter.csgoempire_restart_bots_global_time))
        threads_list.append(restart_bots_thread)

    if manager.csgoempire_steam_cancel_offers_global_time != 0:  # Steam Cancel Offers
        steam_cancel_offers_thread = threading.Thread(target=manager.create_threads,
                                                      args=('_chk_trd',
                                                            Steam(main_tg_info),
                                                            'steam_cancel_offers',
                                                            'csgoempire_steam_cancel_offers_global_time',
                                                            'csgoempire_thread_function_time',
                                                            'csgoempire_tg_info',
                                                            'csgoempire_steam_cancel_offers_sites_name'))
        threads_list.append(steam_cancel_offers_thread)



    return threads_list


if __name__ == '__main__':
    main_tg_bot = telebot.TeleBot('6710866120:AAElhQPr-4PkOnZvvLDSnYA163Ez0td4KzQ')
    main_tg_info = {
        'tg id': -1001807211917,
        'tg bot': main_tg_bot,
        'bot name': 'CSGOEmpire Seller'}

    try:
        manager = ThreadManager(main_tg_info)
        restarter = Restarter(main_tg_info)

        threads = add_threads(main_tg_info)

        Logs.log(f'CSGOEmpire Seller STARTED ({len(manager.content_acc_data_list)} in Account Data '
                 f'and {len(manager.content_acc_settings_list)} in Account Settings)', '')
        time.sleep(manager.csgoempire_waiting_start_time)
        manager.start_of_work(manager.csgoempire_tg_info, threads, manager.csgoempire_thread_start_time)

    except ServerSelectionTimeoutError as e:
        Logs.notify_except(main_tg_info, f"Script has not started: Connecting to MongoDB ERROR: {e}", '')

    except Exception as e:
        Logs.notify_except(main_tg_info, f"Script has not started: FATAL ERROR: {e}", '')




