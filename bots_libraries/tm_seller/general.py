import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class TMGeneral(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.update_steam_access_token_alert = False

    def update_site_data(self):  # Global Function (class_for_account_functions)
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']
                    tm_apikey = acc_info['tm apikey']
                    token = acc_info['trade url'].split('token=')[1]
                    try:
                        balance_url = f'{self.site_url}/api/v2/set-trade-token?key={tm_apikey}&token=1{token}'
                        response = requests.get(balance_url, timeout=30).json()
                        print(response)
                    except:
                        response = None
                    if response:
                        if 'error' in response and response['error'] == 'invalid trade token, reverify and try again':
                            Logs.notify(self.tg_info, 'Update Site Data: Invalid trade url', username)
                        elif 'token' in response and response['token'] != token:
                            Logs.notify(self.tg_info, 'Update Site Data: Invalid trade url', username)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Site Apikey Global Error: {e}", username)
                time.sleep(10)
            time.sleep(self.update_site_data_global_time)

    def site_apikey(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']
                    tm_apikey = acc_info['tm apikey']
                    try:
                        balance_url = f'{self.site_url}/api/v2/get-money?key={tm_apikey}'
                        response = requests.get(balance_url, timeout=30).json()
                        response_error = response['error']
                    except:
                        response_error = None
                    if response_error and response_error == 'Bad KEY':
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
                api_to_withdraw = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_transfer_apikey']
            except:
                api_to_withdraw = None
            if api_to_withdraw:
                for acc_info in self.content_acc_settings_list:
                    username = None
                    try:
                        username = acc_info['username']
                        tm_apikey = acc_info['tm apikey']
                        try:
                            current_balance_url = f'{self.site_url}/api/v2/get-money?key={tm_apikey}'
                            response = requests.get(current_balance_url, timeout=30).json()
                            response_money = response['money']
                        except:
                            response_money = None
                        if response_money and response_money > 1:
                            time.sleep(3)
                            new_value = round(response_money * 100)
                            try:
                                withdrawing_url = (f'{self.site_url}/api/v2/money-send/{new_value}/{api_to_withdraw}?'
                                                      f'pay_pass=34368&key={tm_apikey}')
                                data = requests.get(withdrawing_url, timeout=30).json()
                                data_error = data['error']
                            except:
                                data_error = None
                            if data_error and data_error == 'need_payment_password':
                                try:
                                    set_pay_password_url = (f'{self.site_url}/api/v2/set-pay-password?'
                                                            f'new_password=34368&key={tm_apikey}')
                                    set_data = requests.get(set_pay_password_url, timeout=30).json()
                                except:
                                    set_data = None
                                if set_data and 'success' in set_data and set_data['success']:
                                    Logs.log(f'Balance Transfer: Payment password has been successfully set', username)
                                elif set_data:
                                    Logs.notify(self.tg_info, 'Balance Transfer: Error to set payment password', username)
                            elif data_error:
                                Logs.notify(self.tg_info, 'Balance Transfer: Wrong payment password', username)
                    except Exception as e:
                        Logs.notify_except(self.tg_info, f"Balance Transfer Global Error: {e}", username)
                    time.sleep(10)
