import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.thread_manager import ThreadManager


class TMGeneral(ThreadManager):
    def __init__(self, name):
        super().__init__(name)

    def validity_tm_apikey(self, tg_info, global_time):
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            username = ''
            for acc_info in self.content_acc_settings_list:
                try:
                    username = acc_info['username']
                    tm_api_key = acc_info['tm apikey']
                    balance_url = f'{self.tm_site_url}/api/v2/get-money?key={tm_api_key}'
                    try:
                        search_response = requests.get(balance_url, timeout=30).json()
                    except:
                        continue
                    if 'error' in search_response and search_response['error'] == 'Bad KEY':
                        Logs.notify(tg_info, 'Site Apikey: Invalid apikey', username)
                except Exception as e:
                    Logs.notify_except(tg_info, f"Site Apikey Global Error: {e}", username)
                time.sleep(10)
                username = ''
            time.sleep(global_time)

    def transfer_balance(self, tg_info, global_time):
        Logs.log(f"Balance Transfer: thread are running", '')
        while True:
            self.update_account_settings_info()
            username = ''
            try:
                api_to_withdraw = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_transfer_apikey']
            except:
                api_to_withdraw = None
            if api_to_withdraw:
                for acc in self.content_acc_settings_list:
                    try:
                        username = acc['username']
                        tm_api = acc['tm apikey']
                        current_balance_url = f'{self.tm_site_url}/api/v2/get-money?key={tm_api}'
                        try:
                            response = requests.get(current_balance_url, timeout=30).json()
                        except:
                            continue
                        if 'money' in response and response['money'] > 1:
                            time.sleep(3)
                            new_value = round(response['money'] * 100)
                            withdrawing_tm_url = (f'{self.tm_site_url}/api/v2/money-send/{new_value}/{api_to_withdraw}?'
                                                  f'pay_pass=34368&key={tm_api}')
                            try:
                                data = requests.get(withdrawing_tm_url, timeout=30).json()
                            except:
                                continue
                            if 'error' in data and data['error'] == 'need_payment_password':
                                set_pay_password_url = (f'{self.tm_site_url}/api/v2/set-pay-password?'
                                                        f'new_password=34368&key={tm_api}')
                                try:
                                    data_ = requests.get(set_pay_password_url, timeout=30).json()
                                except:
                                    continue
                                if 'success' in data_ and data_['success']:
                                    Logs.log(f'Balance Transfer: Payment password has been successfully set', username)
                                else:
                                    Logs.notify(tg_info, 'Balance Transfer: Error to set payment password', username)
                            else:
                                Logs.notify(tg_info, 'Balance Transfer: Wrong payment password', username)
                    except Exception as e:
                        Logs.log_except(f"Balance Transfer Global Error: {e}", username)
                    time.sleep(10)
                    username = ''
            time.sleep(global_time)
