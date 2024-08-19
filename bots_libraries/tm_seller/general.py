import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.thread_manager import ThreadManager


class TMGeneral(ThreadManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    def site_apikey(self, global_time):
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']
                    tm_apikey = acc_info['tm apikey']
                    try:
                        balance_url = f'{self.tm_site_url}/api/v2/get-money?key={tm_apikey}'
                        search_response = requests.get(balance_url, timeout=30).json()
                    except:
                        search_response = None
                    if search_response and 'error' in search_response and search_response['error'] == 'Bad KEY':
                        Logs.notify(self.tg_info, 'Site Apikey: Invalid apikey', username)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Site Apikey Global Error: {e}", username)
                time.sleep(10)
            time.sleep(global_time)

    def balance_transfer(self, global_time):
        Logs.log(f"Balance Transfer: thread are running", '')
        while True:
            time.sleep(global_time)
            self.update_account_settings_info()
            self.update_database_info(prices=False)
            try:
                api_to_withdraw = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_transfer_apikey']
            except:
                api_to_withdraw = None
            if api_to_withdraw:
                for acc in self.content_acc_settings_list:
                    username = None
                    try:
                        username = acc['username']
                        tm_apikey = acc['tm apikey']
                        try:
                            current_balance_url = f'{self.tm_site_url}/api/v2/get-money?key={tm_apikey}'
                            response = requests.get(current_balance_url, timeout=30).json()
                        except:
                            response = None
                        if response and 'money' in response and response['money'] > 1:
                            time.sleep(3)
                            new_value = round(response['money'] * 100)
                            try:
                                withdrawing_tm_url = (f'{self.tm_site_url}/api/v2/money-send/{new_value}/{api_to_withdraw}?'
                                                      f'pay_pass=34368&key={tm_apikey}')
                                data = requests.get(withdrawing_tm_url, timeout=30).json()
                            except:
                                data = None
                            if data and 'error' in data and data['error'] == 'need_payment_password':
                                try:
                                    set_pay_password_url = (f'{self.tm_site_url}/api/v2/set-pay-password?'
                                                            f'new_password=34368&key={tm_apikey}')
                                    data_ = requests.get(set_pay_password_url, timeout=30).json()
                                except:
                                    data_ = None
                                if data_ and 'success' in data_ and data_['success']:
                                    Logs.log(f'Balance Transfer: Payment password has been successfully set', username)
                                elif data_:
                                    Logs.notify(self.tg_info, 'Balance Transfer: Error to set payment password', username)
                            else:
                                Logs.notify(self.tg_info, 'Balance Transfer: Wrong payment password', username)
                    except Exception as e:
                        Logs.log_except(f"Balance Transfer Global Error: {e}", username)
                    time.sleep(10)

