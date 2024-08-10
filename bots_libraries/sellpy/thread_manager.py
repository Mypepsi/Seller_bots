import re
import time
import threading
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam


class ThreadManager(Steam):
    def __init__(self, name):
        super().__init__(name)


    def start_of_work(self, tg_info, threads, thread_start_time):
        for thread in threads:
            try:
                thread.start()
                time.sleep(thread_start_time)
            except Exception as e:
                modified_desired_key = 'Failed to get name'
                try:
                    match = re.search(r'\((.*?)\)', thread.name)
                    if match:
                        desired_key = match.group(1)
                        modified_desired_key = desired_key.replace("_", " ").title()
                except:
                    pass
                Logs.notify_except(tg_info, f"{modified_desired_key}: Thread has not started: {e}", '')

    def create_threads(self, name_func, class_obj, func, global_time, thread_function_time, tg_info,
                       cancel_offers_sites_name=None):
        counter = 0
        modified_function_name = func.replace("_", " ").title()
        username = ''
        for i in self.content_acc_data_list:
            try:
                username = str(i['username'])
                name = username + name_func
                globals()[name] = class_obj
                func_to_call = getattr(class_obj, func)
                if cancel_offers_sites_name is None:
                    thread = threading.Thread(target=func_to_call,
                                              args=(i, getattr(class_obj, tg_info),
                                                    getattr(class_obj, global_time)))
                else:
                    thread = threading.Thread(target=func_to_call,
                                              args=(i, getattr(class_obj, tg_info),
                                                    getattr(class_obj, global_time),
                                                    getattr(class_obj, cancel_offers_sites_name)))
                thread.start()
                counter += 1
                time.sleep(getattr(class_obj, thread_function_time))
            except Exception as e:
                Logs.notify_except(tg_info, f"{modified_function_name}: Thread for Account has not created: {e}", username)
        Logs.log(f"{modified_function_name}: {counter} threads are running", '')