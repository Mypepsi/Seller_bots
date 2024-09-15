import io
import jwt
import time
import pickle
from bots_libraries.sellpy.mongo import Mongo
from bots_libraries.steampy.client import SteamClient
from bots_libraries.sellpy.logs import Logs, ExitException


class SessionManager(Mongo):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.active_session = False
        self.steamclient = SteamClient('')

        self.trade_url = None
        self.tm_apikey = None
        self.waxpeer_apikey = None
        self.csgoempire_apikey = None
        self.csgoempire_headers = None
        self.csgo500_user_id = self.csgo500_apikey = None
        self.jwt_api_key = None
        self.csgo500_jwt_apikey = None
        self.shadowpay_apikey = None
        self.buff_cookie = None

        self.steam_inventory_tradable = self.steam_inventory_full = self.steam_inventory_phases = {}

    # region Session
    def update_session(self, acc_info):  # Global Function (class_for_account_functions)
        while True:
            self.update_account_settings_info()
            self.update_account_data_info()
            self.active_session = self.take_session(acc_info)
            time.sleep(self.update_session_global_time)

    def take_session(self, acc_info):
        username = None
        try:
            if 'username' in acc_info:
                username = acc_info['username']
                if 'steam session' in acc_info:
                    session = acc_info['steam session']
                else:
                    if username in self.content_acc_data_dict and 'steam session' in self.content_acc_data_dict[username]:
                        session = self.content_acc_data_dict[username]['steam session']
                    else:
                        return False
                steam_cookie_file = io.BytesIO(session)
                self.steamclient = pickle.load(steam_cookie_file)
                self.acc_history_collection = self.get_collection(self.seller_history,
                                                                  f'history_{self.steamclient.username}')

                # Info from account_settings
                proxy = self.content_acc_settings_dict[self.steamclient.username]['proxy']
                if proxy == "proxy":
                    proxies = None
                else:
                    proxy_list = proxy.split(':')
                    proxy_ip = proxy_list[0]
                    proxy_port = proxy_list[1]
                    proxy_login = proxy_list[2]
                    proxy_password = proxy_list[3]
                    proxies = {'http': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}',
                               'https': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}'}
                self.steamclient.proxies = proxies
                self.steamclient.session.proxies.update(self.steamclient.proxies)
                self.trade_url = self.content_acc_settings_dict[self.steamclient.username]['trade url']
                self.tm_apikey = self.content_acc_settings_dict[self.steamclient.username]['tm apikey']
                self.waxpeer_apikey = self.content_acc_settings_dict[self.steamclient.username]['waxpeer apikey']
                self.csgoempire_apikey = self.content_acc_settings_dict[self.steamclient.username]['csgoempire apikey']
                self.csgoempire_headers = {
                    'Authorization': f'Bearer {self.csgoempire_apikey}'
                }

                self.jwt_api_key = jwt.encode(
                    {'userId': self.content_acc_settings_dict[self.steamclient.username]['csgo500 user id']},
                    self.content_acc_settings_dict[self.steamclient.username]['csgo500 apikey'],
                    algorithm="HS256"
                )
                self.csgo500_jwt_apikey = {'x-500-auth': self.jwt_api_key}
                self.shadowpay_apikey = self.content_acc_settings_dict[self.steamclient.username]['shadowpay apikey']
                raw_cookies = self.content_acc_settings_dict[self.steamclient.username]['buff cookie']
                if raw_cookies:
                    self.buff_cookie = dict(pair.split("=", 1) for pair in raw_cookies.split("; "))
                else:
                    self.buff_cookie = None

                # Info from account_data
                self.steamclient._api_key = self.content_acc_data_dict[self.steamclient.username]['steam apikey']
                self.steam_inventory_tradable = (
                    self.content_acc_data_dict)[self.steamclient.username]['steam inventory tradable']
                self.steam_inventory_full = (
                    self.content_acc_data_dict)[self.steamclient.username]['steam inventory full']
                self.steam_inventory_phases = (
                    self.content_acc_data_dict)[self.steamclient.username]['steam inventory phases']

                return True
            else:
                raise ExitException
        except Exception as e:
            Logs.notify_except(self.tg_info, f'MongoDB: Error while taking Account Session: {e}', username)
            return False
    # endregion
