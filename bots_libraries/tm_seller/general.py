from bots_libraries.base_info.logs import Logs, ExitException
from bots_libraries.base_info.thread_manager import ThreadManager
import math
import json
import time
import requests


class TMGeneral(ThreadManager):
    def __init__(self):
        super().__init__()

    def validity_tm_apikey(self):
        for acc_info in self.content_acc_list:
            time.sleep(10)
            try:
                username = acc_info['username']
                tm_api_key = acc_info['tm apikey']
                balance_url = f'https://{self.tm_url}/api/v2/get-money?key={tm_api_key}'
                try:
                    search_response = requests.get(balance_url, timeout=30).json()
                except:
                    continue
                if 'error' in search_response and search_response['error'] == 'Bad KEY':
                    Logs.log_and_send_msg_in_tg(self.tm_tg_info, 'TM API key Error', username)
            except:
                pass
            Logs.log(f'TM API key: All TM API key checked')

    def transfer_balance(self):
        api_to_withdraw = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_transfer_apikey']
        for acc in self.content_acc_list:
            time.sleep(10)
            try:
                username = acc['username']
                tm_api = acc['tm apikey']
                current_balance_url = f'https://{self.tm_url}/api/v2/get-money?key={tm_api}'
                try:
                    response = requests.get(current_balance_url, timeout=30).json()
                except:
                    continue
                balance_tm = response['money']
                if balance_tm > 1:
                    time.sleep(3)
                    new_value = round(balance_tm * 100)
                    withdrawing_tm_url = (f'https://{self.tm_url}/api/v2/money-send/{new_value}/{api_to_withdraw}?'
                                          f'pay_pass=34368&key={tm_api}')
                    try:
                        data = requests.get(withdrawing_tm_url, timeout=30).json()
                    except:
                        continue
                    if 'error' in data and data['error'] == 'need_payment_password':
                        set_pay_password_url = (f'https://{self.tm_url}/api/v2/set-pay-password?'
                                                f'new_password=34368&key={tm_api}')
                        try:
                            data_ = requests.get(set_pay_password_url, timeout=30).json()
                        except:
                            continue
                        if 'success' in data_ and data_['success']:
                            Logs.log(f'{username}: payment password has been successfully set')
                        else:
                            Logs.log_and_send_msg_in_tg(self.tm_tg_info, 'Money Transfer: '
                                                                         'Error to set payment password', username)
                    else:
                        Logs.log_and_send_msg_in_tg(self.tm_tg_info, 'Money Transfer: Wrong payment password',
                                                    username)
            except:
                pass
        Logs.log(f'Money Transfer: Balance from all accounts transferred')
