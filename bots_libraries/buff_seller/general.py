import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class BuffGeneral(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    def update_site_data(self):  # Global Function (class_for_account_functions)
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']
                    raw_cookies = acc_info['buff cookie']
                    buff_cookie = dict(pair.split('=') for pair in raw_cookies.split('; ') if '=' in pair)
                    buff_cookie['Locale-Supported'] = 'en'
                    trade_url = acc_info['trade url']
                    steam_apikey = self.content_acc_data_dict[username]['steam apikey']

                    headers = {
                        "Host": "buff.163.com",
                        "Origin": "https://buff.163.com",
                        "Referer": "https://buff.163.com/user-center/profile",
                        "X-CSRFToken": buff_cookie.get("csrf_token")
                    }
                    try:
                        trade_url_data = {"trade_url": trade_url}
                        tradelink_url = f'{self.site_url}/api/market/steam/trade_url'
                        requests.post(tradelink_url, json=trade_url_data, headers=headers, timeout=15)
                    except:
                        pass

                    time.sleep(1)
                    if steam_apikey:
                        steam_apikey_data = {
                            'api_key': steam_apikey
                        }
                        try:
                            apikey_url = f'{self.site_url}/account/api/steam_api_key_raw'
                            requests.post(apikey_url, json=steam_apikey_data, headers=headers, timeout=15)
                        except:
                            pass
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Update Site Data Global Error: {e}", username)
                time.sleep(3)
            time.sleep(self.update_site_data_global_time)

    def site_cookie(self):  # Global Function (class_for_account_functions)
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']

                    raw_cookies = acc_info['buff cookie']
                    buff_cookie = dict(pair.split('=') for pair in raw_cookies.split('; ') if '=' in pair)
                    buff_cookie['Locale-Supported'] = 'en'

                    headers = {
                        "Host": "buff.163.com",
                        "Origin": "https://buff.163.com",
                        "Referer": "https://buff.163.com/user-center/profile",
                        "X-CSRFToken": buff_cookie.get("csrf_token")
                    }
                    try:
                        cookies_url = f'{self.site_url}/api/asset/get_brief_asset/?_={int(time.time() * 1000)}'
                        response = requests.get(cookies_url, headers=headers, cookies=buff_cookie, timeout=15)
                    except:
                        response = None
                    try:
                        response_json = response.json()
                    except:
                        response_json = None
                    if response and response_json is None and response.status_code == 200:
                        Logs.notify(self.tg_info, 'Site Cookies: Invalid  buff cookies', username)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Update Site Data Global Error: {e}", username)
                time.sleep(10)
            time.sleep(self.site_cookie_global_time)
