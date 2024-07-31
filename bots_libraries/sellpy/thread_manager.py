import time
import requests
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam


class ThreadManager(Steam):
    def __init__(self):
        super().__init__()

    def start_of_work(self, tg_info, threads, sleep_between_threads):
        for thread in threads:
            try:
                thread.start()
                time.sleep(sleep_between_threads)
            except Exception as e:
                modified_desired_key = 'Failed to get name'

                try:
                    for key, value in globals().items():
                        if hasattr(value, 'name') and value.name == thread.name:
                            desired_key = key
                            modified_desired_key = desired_key.replace("_", " ").title()
                            break
                except:
                    pass
                Logs.notify_except(tg_info, f'{modified_desired_key}: Thread has not started: {e}',
                                   self.steamclient.username)

    def create_threads(self, name_func, class_obj, func, global_sleep, thread_function_sleep,
                       cancel_offers_sites_name=None):
        counter = 0
        modified_function_name = func.replace("_", " ").title()
        for i in self.content_acc_data_list:
            username = str(i['username'])
            try:
                name = username + name_func
                globals()[name] = class_obj
                func_to_call = getattr(class_obj, func)
                if cancel_offers_sites_name is None:
                    thread = threading.Thread(target=func_to_call, args=(i, getattr(class_obj, global_sleep)))
                else:
                    thread = threading.Thread(target=func_to_call, args=(i, getattr(class_obj, global_sleep),
                                                                         getattr(class_obj, cancel_offers_sites_name)))

                thread.start()
                counter += 1
                time.sleep(getattr(class_obj, thread_function_sleep))
            except Exception as e:
                Logs.log_except(f'{modified_function_name}: Thread for Account has not created: {e}',
                                self.steamclient.username)
        Logs.log(f'{modified_function_name}: {counter} threads are running', '')

    def create_threads_with_acc_data(self, function, time_sleep, sleep_in_the_end=True):
        while True:
            if not sleep_in_the_end:
                time.sleep(time_sleep)
            for acc in self.content_acc_data_list:
                self.take_session(acc)
                self.steamclient.username = acc['username']
                function()
            modified_function_name = function.__name__.replace("_", " ").title()
            Logs.log(f'{modified_function_name}: All accounts parsed')
            if sleep_in_the_end:
                time.sleep(time_sleep)

    @staticmethod
    def create_threads_with_loop(function, time_sleep):
        while True:
            function()
            time.sleep(time_sleep)

