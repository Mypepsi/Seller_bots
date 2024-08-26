import time
import threading
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.mongo import Mongo


class ThreadManager(Mongo):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.dict_for_accounts = {}

    def start_of_work(self, functions):
        dict_for_classes = {}
        for function in functions:
            modified_function_name = 'Function not found'
            try:
                func = function['func']
                modified_function_name = func.replace("_", " ").title()
                if "class_for_single_function" in function:
                    class_obj = function["class_for_single_function"](self.tg_info)
                elif "class_for_many_functions" in function:
                    class_name = function["class_for_many_functions"]
                    if class_name not in dict_for_classes:
                        dict_for_classes[class_name] = class_name(self.tg_info)
                    class_obj = dict_for_classes[class_name]
                elif "class_for_account_functions" in function:
                    account_thread = threading.Thread(target=self.create_threads,
                                                      args=(function,
                                                            modified_function_name))
                    account_thread.start()
                    continue
                else:
                    raise ExitException
                func_to_call = getattr(class_obj, func)
                thread = threading.Thread(target=func_to_call)
                thread.start()
                time.sleep(self.thread_start_time)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"{modified_function_name}: Thread has not started: {e}", '')

    def create_threads(self, function, modified_function_name):
        counter = 0
        try:
            username = ''
            for acc in self.content_acc_data_list:
                try:
                    username = str(acc['username'])
                    funct = function["func"]
                    class_name = function["class_for_account_functions"]
                    if username not in self.dict_for_accounts or class_name not in self.dict_for_accounts[username]:
                        class_obj = class_name(self.tg_info)
                        self.dict_for_accounts[username][class_name] = class_obj
                        update_session_to_call = getattr(class_obj, "update_session")
                        thread = threading.Thread(target=update_session_to_call, args=acc)
                        thread.start()
                        time.sleep(1)
                    else:
                        class_obj = self.dict_for_accounts[username][class_name]
                    time.sleep(1)
                    func_to_call = getattr(class_obj, funct)
                    thread = threading.Thread(target=func_to_call)
                    thread.start()
                    counter += 1
                    time.sleep(self.thread_function_time)
                except Exception as e:
                    Logs.notify_except(self.tg_info,
                                       f"{modified_function_name}: Function for Account has not created: {e}",
                                       username)
        except Exception as e:
            Logs.notify_except(self.tg_info,
                               f"{modified_function_name}: Error in handling account functions: {e}", '')
        Logs.log(f"{modified_function_name}: {counter} threads are running", '')
