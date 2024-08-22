import re
import time
import threading
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.mongo import Mongo


class ThreadManager(Mongo):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    def start_of_work(self, functions, thread_function_time, thread_start_time):
        instances_per_functions = {}
        instances_per_functions_and_account = {}
        modified_desired_key = ''
        for function in functions:
            try:
                func = function['func']
                modified_desired_key = func.replace("_", " ").title()
                if "class_per_functions" in function:
                    class_key = "class_per_functions"
                    class_name = function[class_key]
                    if class_name not in instances_per_functions:
                        instances_per_functions[class_name] = class_name(function["tg_info"])
                    function[class_key] = instances_per_functions[class_name]
                elif "class_name" in function:
                    class_key = "class_name"
                    function[class_key] = function[class_key](function["tg_info"])
                elif "class_per_functions_and_account" in function:
                    username = ''
                    for i in self.content_acc_data_list:
                        try:
                            username = str(i['username'])
                            funct = function["func"]
                            if username not in instances_per_functions_and_account:
                                class_obj = function["class_per_functions_and_account"](function["tg_info"])
                                instances_per_functions[username] = class_obj
                            else:
                                class_obj = instances_per_functions[username]
                            func_to_call = getattr(class_obj, funct)
                            thread = threading.Thread(target=func_to_call, args=i)
                            thread.start()
                            time.sleep(thread_function_time)
                        except Exception as e:
                            Logs.notify_except(self.tg_info,
                                               f"{modified_desired_key}: Thread for Account has not created: {e}",
                                               username)
                    continue
                else:
                    raise ExitException
                func_to_call = getattr(function[class_key], func)
                thread = threading.Thread(target=func_to_call)
                thread.start()
                time.sleep(thread_start_time)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"{modified_desired_key}: Thread has not started: {e}", '')

