from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.mongo import Mongo
from bots_libraries.steampy.client import SteamClient
from fake_useragent import UserAgent
import pickle
import io
import time
import threading
import requests


class Steam(Mongo):
    def __init__(self):
        super().__init__()

        self.questionable_proxies = {}
        self.ua = UserAgent()

    def take_session(self, steam_session):
        i = steam_session
        steam_cookie_file = io.BytesIO(i)
        self.steamclient = pickle.load(steam_cookie_file)
        self.steamclient.tm_api = self.content_acc_dict[self.steamclient.username]['tm apikey']

    def work_with_steam_settings(self, function, time_sleep):
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

    def work_with_steam_data(self, function, time_sleep):
        while True:
            self.update_account_data_info()
            for acc in self.content_acc_data_list:
                self.steamclient.username = acc['username']
                steam_session = acc['steam session']
                self.take_session(steam_session)
                function()
            modified_function_name = function.__name__.replace("_", " ").title()
            Logs.log(f'{modified_function_name}: All accounts parsed ({len(self.content_acc_data_list)} accounts in MongoDB)')
            time.sleep(time_sleep)

    def work_with_steam_loop(self, function, time_sleep):
        while True:
            self.update_account_data_info()
            function()
            time.sleep(time_sleep)

    def work_with_steam_create_thread(self, function, function_time_sleep, thread_time_sleep):
        self.update_account_data_info()
        counter = 0
        for acc in self.content_acc_data_list:
            thread = threading.Thread(target=function, args=(acc, function_time_sleep))
            thread.start()
            counter += 1
            time.sleep(thread_time_sleep)
        modified_function_name = function.__name__.replace("_", " ").title()
        Logs.log(f'{modified_function_name}: {counter} threads are running '
                 f'({len(self.content_acc_data_list)} accounts in MongoDB)')







