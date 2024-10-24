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

    def balance_transfer(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Balance Transfer: thread are running", '')
        while True:
            time.sleep(self.balance_transfer_global_time)
            self.update_account_settings_info()
            self.update_database_info(settings=True)
            try:
                amount_to_withdraw = self.content_database_settings['DataBaseSettings']['ShadowPay_Seller'][
                    'ShadowPay_Seller_transfer_amount']
            except:
                amount_to_withdraw = None
            if amount_to_withdraw:
                for acc_info in self.content_acc_settings_list:
                    username = None
                    try:
                        username = acc_info['username']
                        shadowpay_apikey = acc_info['shadowpay apikey']
                        try:
                            current_balance_url = f'{self.site_url}/api/v2/user/balance'
                            headers = {
                                "Token": shadowpay_apikey
                            }
                            response = requests.get(current_balance_url, headers=headers, timeout=15).json()
                            response_money = response['data']['balance']
                        except:
                            response_money = None
                        if response_money and response_money > amount_to_withdraw:
                            Logs.notify(self.tg_info, f"Balance Transfer: Current balance: {response_money}$", username)
                    except Exception as e:
                        Logs.notify_except(self.tg_info, f"Balance Transfer Global Error: {e}", username)
                    time.sleep(10)

