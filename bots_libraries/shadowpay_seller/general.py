import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class ShadowPayGeneral(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    def site_apikey(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']
                    headers = {"Authorization": f"Bearer {acc_info['shadowpay apikey']}"}
                    try:
                        balance_url = f'{self.site_url}/api/v2/user/balance'
                        response = requests.get(balance_url, headers=headers, timeout=15).json()
                    except:
                        response = None
                    if response and 'error_message' in response and response['error_message'] == 'need_auth':
                        Logs.notify(self.tg_info, 'Site Apikey: Invalid apikey', username)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Site Apikey Global Error: {e}", username)
                time.sleep(10)
            time.sleep(self.site_apikey_global_time)
