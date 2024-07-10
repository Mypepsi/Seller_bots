from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.steam import Steam
from bots_libraries.steampy.client import SteamClient
import time
import requests
import threading


class ThreadManager(Steam):
    def __init__(self):
        super().__init__()

    def start_of_work(self, threads, sleep_between_threads):
        for thread in threads:
            try:
                thread.start()
                time.sleep(sleep_between_threads)
            except Exception as e:
                desired_key = ''
                for key, value in globals().items():
                    if hasattr(value, 'name') and value.name == thread.name:
                        desired_key = key
                        break
                self.error_alert(desired_key, e)
        Logs.log('All bot functions are running')

    def create_threads(self, name_func, class_obj, func, global_sleep, thread_function_sleep):
        self.update_account_data_info()
        counter = 0
        func_to_call = ''
        for i in self.content_acc_data_list:
            username = str(i['username'])
            name = username + name_func
            globals()[name] = class_obj
            func_to_call = getattr(class_obj, func)
            thread = threading.Thread(target=func_to_call, args=(i, getattr(class_obj, global_sleep)))
            thread.start()
            counter += 1
            time.sleep(getattr(class_obj, thread_function_sleep))
        modified_function_name = func_to_call.__name__.replace("_", " ").title()
        Logs.log(f'{modified_function_name}: {counter} threads are running '
                 f'({len(self.content_acc_data_list)} accounts in MongoDB)')

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
                f'{modified_function_name}: All accounts authorized ({len(self.content_acc_list)} accounts in MongoDB)')
            time.sleep(time_sleep)

    def create_threads_with_acc_data(self, function, time_sleep, sleep_in_the_end=True):
        while True:
            self.update_account_data_info()
            if not sleep_in_the_end:
                time.sleep(time_sleep)
            for acc in self.content_acc_data_list:
                steam_session = acc['steam session']
                self.take_session(steam_session)
                self.steamclient.username = acc['username']
                function()
            modified_function_name = function.__name__.replace("_", " ").title()
            Logs.log(f'{modified_function_name}: All accounts parsed ({len(self.content_acc_data_list)} accounts in MongoDB)')
            if sleep_in_the_end:
                time.sleep(time_sleep)

    @staticmethod
    def create_threads_with_loop(function, time_sleep):
        while True:
            function()
            time.sleep(time_sleep)
