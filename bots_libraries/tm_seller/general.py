from bots_libraries.base_info.logs import Logs, ExitException
from bots_libraries.base_info.thread_manager import ThreadManager
import math
import json
import time
import requests


class TMGeneral(ThreadManager):
    def __init__(self):
        super().__init__()

    def validity_tm_apikey(self, time_sleep):
        while True:
            for acc_info in self.content_acc_list:
                try:
                    username = acc_info['username']
                    tm_api_key = acc_info['tm apikey']
                    balance_url = f'https://market.csgo.com/api/v2/get-money?key={tm_api_key}'
                    try:
                        search_response = requests.get(balance_url, timeout=30).json()
                    except:
                        search_response = None
                    if (search_response is not None
                            and 'error' in search_response and search_response['error'] == 'Bad KEY'):
                        Logs.log(f'{username}: TM API key Error')
                        self.tm_tg_bot.send_message(self.tm_tg_id, f'TM Seller: TM API key Error: {username}')
                except:
                    pass
                time.sleep(10)

            Logs.log(f'TM API key: All TM API key checked ({len(self.content_acc_list)} accounts in MongoDB)')
            time.sleep(time_sleep)

    def transfer_balance(self):
        api_to_withdraw = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_transfer_apikey']

        for acc in self.content_acc_list:
            try:
                username = acc['username']
                tm_api = acc['tm apikey']
                current_balance_url = f'https://market.csgo.com/api/v2/get-money?key={tm_api}'
                try:
                    response = requests.get(current_balance_url, timeout=30)
                except:
                    raise
                if response.status_code == 200:
                    data = json.loads(response.text)
                    money_value = data['money']
                    balance_tm = math.floor(money_value)
                    if balance_tm > 0:
                        time.sleep(3)
                        new_value = balance_tm * 100
                        withdrawing_tm_url = (f'https://market.csgo.com/api/v2/money-send/{new_value}/{api_to_withdraw}?'
                                              f'pay_pass=34368&key={tm_api}')
                        try:
                            response = requests.get(withdrawing_tm_url, timeout=30)
                        except:
                            raise
                        if response.status_code == 200:
                            data = json.loads(response.text)
                            if 'amount' in data:
                                withdraw_money = data['amount'] / 100
                                Logs.log(f'{username}: {withdraw_money}: RUB transferred')
                            if 'error' in data and data['error'] == 'wrong_payment_password':
                                set_pay_password_url = (f'https://market.csgo.com/api/v2/set-pay-password?'
                                                        f'new_password=34368&key={tm_api}')
                                try:
                                    response = requests.get(set_pay_password_url, timeout=30)
                                except:
                                    raise
                                if response.status_code == 200:
                                    data = json.loads(response.text)
                                    if 'success' in data and data['success']:
                                        Logs.log(f'{username}: payment password has been successfully set')
            except:
                pass
