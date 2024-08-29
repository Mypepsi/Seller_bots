import time
import threading
from bots_libraries.sellpy.mongo import Mongo
from bots_libraries.sellpy.logs import Logs, ExitException


class ThreadManager(Mongo):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.dict_for_accounts = {}
        self.dict_for_classes = {}


    def start_work_functions(self, functions):
        for function in functions:
            modified_function_name = 'Function not found'
            try:
                func = function['func']
                modified_function_name = func.replace("_", " ").title()
                if "class_for_single_function" in function:
                    class_obj = function["class_for_single_function"](self.tg_info)
                    ThreadManager.create_work_threads(class_obj, func)
                elif "class_for_many_functions" in function:
                    class_name = function["class_for_many_functions"]
                    if class_name not in self.dict_for_classes:
                        self.dict_for_classes[class_name] = class_name(self.tg_info)
                    class_obj = self.dict_for_classes[class_name]
                    ThreadManager.create_work_threads(class_obj, func)
                elif "class_for_account_functions" in function:
                    class_name = function["class_for_account_functions"]
                    ThreadManager.create_work_threads(self, 'manage_work_accounts', args=(func,
                                                                                          class_name,
                                                                                          modified_function_name))
                else:
                    raise ExitException
            except Exception as e:
                Logs.notify_except(self.tg_info, f"{modified_function_name}: Function has not started: {e}", '')
            time.sleep(self.function_start_time)

    def manage_work_accounts(self, func, class_name, modified_function_name):
        counter = 0
        for acc in self.content_acc_data_list:
            username = None
            try:
                username = acc['username']
                if username not in self.dict_for_accounts:
                    self.dict_for_accounts[username] = {}
                if class_name not in self.dict_for_accounts[username]:
                    class_obj = class_name(self.tg_info)
                    self.dict_for_accounts[username][class_name] = class_obj
                    ThreadManager.create_work_threads(class_obj, "update_session", args=(acc,))
                    time.sleep(1)
                else:
                    class_obj = self.dict_for_accounts[username][class_name]
                ThreadManager.create_work_threads(class_obj, func)
                counter += 1
            except Exception as e:
                Logs.notify_except(self.tg_info,
                                   f"{modified_function_name}: Function for Account has not started: {e}",
                                   username)
            time.sleep(self.account_start_time)
        Logs.log(f"{modified_function_name}: {counter} threads are running", '')

    @staticmethod
    def create_work_threads(class_obj, func: str, args=None):
        func_to_call = getattr(class_obj, func)
        if args:
            thread = threading.Thread(target=func_to_call, args=args)
        else:
            thread = threading.Thread(target=func_to_call)
        thread.start()
