import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class WaxpeerGeneral(SteamManager):
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
                    waxpeer_apikey = acc_info['waxpeer apikey']
                    trade_url = acc_info['trade url']
                    steam_apikey = self.content_acc_data_dict[username]['steam apikey']
                    try:
                        data = {"tradelink": trade_url}
                        tradelink_url = f'{self.site_url}/v1/change-tradelink?api={waxpeer_apikey}'
                        tradelink_response = requests.post(tradelink_url, data=data, timeout=15).json()
                    except:
                        tradelink_response = None
                    if (tradelink_response and 'msg' in tradelink_response
                            and tradelink_response['msg'] == 'Your tradelink is incorect, please update it'):
                        Logs.notify(self.tg_info, f"Update Site Data: Invalid trade url: {tradelink_response['msg']}",
                                    username)
                    if steam_apikey:
                        try:
                            apikey_url = (f'{self.site_url}/v1/set-my-steamapi?api={waxpeer_apikey}'
                                          f'&steam_api={steam_apikey}')
                            apikey_response = requests.get(apikey_url, timeout=15).json()
                        except:
                            apikey_response = None
                        if apikey_response:
                            if 'msg' in apikey_response and apikey_response['msg'] == 'wrong_api':
                                Logs.notify(self.tg_info, f"Update Site Data: Invalid Steam apikey", username)
                            elif 'api' in apikey_response and apikey_response['api'] != steam_apikey:
                                Logs.notify(self.tg_info, f"Update Site Data: Different Steam apikey", username)

                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Update Site Data Global Error: {e}", username)
                time.sleep(3)
            time.sleep(self.update_site_data_global_time)

    def site_apikey(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']
                    waxpeer_apikey = acc_info['waxpeer apikey']
                    try:
                        balance_url = f'{self.site_url}/api/v1/user?api={waxpeer_apikey}'
                        response = requests.get(balance_url, timeout=15).json()
                    except:
                        response = None
                    if response and 'msg' in response and response['msg'] == 'wrong api':
                        Logs.notify(self.tg_info, 'Site Apikey: Invalid apikey', username)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Site Apikey Global Error: {e}", username)
                time.sleep(10)
            time.sleep(self.site_apikey_global_time)
