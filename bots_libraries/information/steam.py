from bots_libraries.information.logs import Logs
from bots_libraries.information.mongo import Mongo
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

        self.username_title = 'username'
        self.password_title = 'password'
        self.steam_id_title = 'steam id'
        self.shared_secret_title = 'shared secret'
        self.identity_secret_title = 'identity secret'
        self.proxy_title = 'proxy'
        self.questionable_proxies = {}

        self.ua = UserAgent()


    def take_session(self, steam_session):
        i = steam_session
        steam_cookie_file = io.BytesIO(i)
        self.steamclient = pickle.load(steam_cookie_file)

    def work_with_steam_settings(self, function, time_sleep):
        while True:
            self.update_mongo_info()
            for acc in self.content_accs:
                try:
                    username = acc['username']
                    session = self.content_accs_parsed_dict[username]['steam session']
                    self.take_session(session)
                    self.user_agent = self.steamclient.user_agent
                except:
                    self.user_agent = self.ua.random
                self.steamclient = SteamClient('', user_agent=self.user_agent)

                self.username = acc[self.username_title]
                self.password = acc[self.password_title]
                self.steam_id = acc[self.steam_id_title]
                self.shared_secret = acc[self.shared_secret_title]
                self.identity_secret = acc[self.identity_secret_title]
                self.steam_guard = {"steamid": self.steam_id,
                                    "shared_secret": self.shared_secret,
                                    "identity_secret": self.identity_secret
                                    }


                proxy = acc[self.proxy_title]
                if proxy == "proxy":
                    self.proxy = {"NoProxy": 1}
                else:
                    proxy_list = proxy.split(':')
                    proxy_ip = proxy_list[0]
                    proxy_port = proxy_list[1]
                    proxy_login = proxy_list[2]
                    proxy_password = proxy_list[3]

                    self.proxy = {'http': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}',
                                  'https': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}'}


                function()
            modified_function_name = function.__name__.replace("_", " ").title()
            Logs.log(
                f'{modified_function_name}: All accounts authorized ({len(self.content_accs)} accounts in MongoDB)')
            time.sleep(time_sleep)

    def work_with_steam_parsed(self, function, time_sleep):
        while True:
            self.update_mongo_info()
            for acc in self.content_accs_parsed_list:
                self.username = acc['username']
                steam_session = acc['steam session']
                self.take_session(steam_session)
                function()
            modified_function_name = function.__name__.replace("_", " ").title()
            Logs.log(f'{modified_function_name}: All accounts parsed ({len(self.content_accs_parsed_list)} accounts in MongoDB)')
            time.sleep(time_sleep)

    def work_with_steam_loop(self, function, time_sleep):
        while True:
            self.update_mongo_info()
            function()
            # modified_function_name = function.__name__.replace("_", " ").title()
            # Logs.log(
            #     f'Steam {modified_function_name}: All proxy checked ({len(self.proxy_for_check)} proxies)')
            time.sleep(time_sleep)

    # def work_with_steam_create_thread(self, function, time_sleep):
    #
    #     threads = []
    #     print(self.content_accs_parsed_list)
    #     for acc in self.content_accs_parsed_list:
    #         self.username = acc['username']
    #         print(self.username)
    #         steam_session = acc['steam session']
    #         self.take_session(steam_session)
    #         thread = threading.Thread(target=function)
    #         threads.append(thread)
    #
    #     # Запуск потоків
    #     for thread in threads:
    #         thread.start()
    #
    #     # Очікування завершення всіх потоків
    #     for thread in threads:
    #         thread.join()
    #
    #     print(11)



