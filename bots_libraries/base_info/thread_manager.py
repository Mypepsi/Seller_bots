from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.steam import Steam
from bots_libraries.steampy.client import SteamClient
import time
import requests
import threading
import inspect
import os


class ThreadManager(Steam):
    def __init__(self):
        super().__init__()

    def start_of_work(self, threads, sleep_between_threads):
        for thread in threads:
            try:
                thread.start()
                time.sleep(sleep_between_threads)
            except Exception as e:
                modified_desired_key = ''
                for key, value in globals().items():
                    if hasattr(value, 'name') and value.name == thread.name:
                        desired_key = key
                        modified_desired_key = desired_key.replace("_", " ").title()
                        break
                self.error_alert(modified_desired_key, e)

    def create_threads(self, name_func, class_obj, func, global_sleep, thread_function_sleep):
        self.update_account_data_info()
        counter = 0
        modified_function_name = func.replace("_", " ").title()
        for i in self.content_acc_data_list:
            username = str(i['username'])
            try:
                name = username + name_func
                globals()[name] = class_obj
                func_to_call = getattr(class_obj, func)
                thread = threading.Thread(target=func_to_call, args=(i, getattr(class_obj, global_sleep)))
                thread.start()
                counter += 1
                time.sleep(getattr(class_obj, thread_function_sleep))
            except:
                Logs.log(f'{modified_function_name}: Error during start: {username}')
        Logs.log(f'{modified_function_name}: {counter} threads are running')

    def create_threads_with_acc_settings(self, function, time_sleep):
        while True:
            self.update_account_data_info()
            for acc in self.content_acc_list:
                try:
                    username = acc['username']
                    session = self.content_acc_data_dict[username]['steam session']
                    self.take_session(session)
                    self.user_agent = self.steamclient.user_agent
                except:
                    self.user_agent = self.ua.random
                self.steamclient = SteamClient('', user_agent=self.user_agent)
                try:
                    self.steamclient.username = acc['username']
                    self.steamclient.password = acc['password']
                    self.steamclient.steam_id = acc['steam id']
                    self.steamclient.shared_secret = acc['shared secret']
                    self.steamclient.identity_secret = acc['identity secret']
                    self.steamclient.steam_guard = {"steamid": self.steamclient.steam_id,
                                        "shared_secret": self.steamclient.shared_secret,
                                        "identity_secret": self.steamclient.identity_secret
                                        }
                    self.steamclient.tm_api = self.get_key(acc, 'tm apikey')
                except Exception as e:
                    Logs.log(f'Error during taking information from account settings: {e}')

                proxy = acc['proxy']
                if proxy == "proxy":
                    self.steamclient.proxies = {"NoProxy": 1}
                else:
                    proxy_list = proxy.split(':')
                    proxy_ip = proxy_list[0]
                    proxy_port = proxy_list[1]
                    proxy_login = proxy_list[2]
                    proxy_password = proxy_list[3]

                    self.steamclient.proxies = {'http': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}',
                                  'https': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}'}

                    requests.proxies = self.steamclient.proxies
                function()
            modified_function_name = function.__name__.replace("_", " ").title()
            Logs.log(
                f'{modified_function_name}: All accounts authorized')
            time.sleep(time_sleep)

    def create_threads_with_acc_data(self, function, time_sleep, sleep_in_the_end=True):
        while True:
            if not sleep_in_the_end:
                time.sleep(time_sleep)
            self.update_account_data_info()
            for acc in self.content_acc_data_list:
                steam_session = acc['steam session']
                self.take_session(steam_session)
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

    def error_alert(self, thread_name: str, error) -> None:
        global threads_alert
        if 'threads_alert' not in globals():
            threads_alert = False

        current_frame = inspect.currentframe()
        caller_frame = inspect.getouterframes(current_frame, 2)[1]
        file_path = caller_frame.filename
        document_name = os.path.splitext(os.path.basename(file_path))[0]

        function_name = thread_name
        modified_function_name = function_name.replace("_", " ").title()
        Logs.log(f'{modified_function_name}: has not started: {error}')
        try:
            acc_setting_first_username = self.content_acc_list[0]['username']
        except:
            acc_setting_first_username = ''
        if not threads_alert:
            self.creator_tg_bot.send_message(self.creator_tg_id,
                                              f'{document_name}: Fatal Error: '
                                              f'threads not running: {acc_setting_first_username}')
            threads_alert = True
