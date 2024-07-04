from bots_libraries.base_info.logs import Logs
from bots_libraries.creator.creator_steam import Steam
import math
import json
import time
import requests
import random
import urllib.parse


class TMOnline(Steam):
    def __init__(self):
        super().__init__()
        self.ping_alert = False

    def request_to_ping(self):
        url = f"https://market.csgo.com/api/v2/ping-new?key=" + self.steamclient.tm_api
        json_data = {
            'access_token': f"{self.steamclient.access_token}"
        }
        if 'http' in self.steamclient.proxies:
            json_data['proxy'] = self.steamclient.proxies['http']

        try:
            response = requests.post(url, json=json_data, timeout=10)
            if response.status_code == 200:
                response_data = response.json()
                if response_data['success'] is False and response_data['message'] != 'too early for pong':
                    Logs.log(f"{self.steamclient.username}: Ping Error: {response_data['message']}")
                    if not self.ping_alert:
                        self.tm_tg_bot.send_message(self.tm_tg_id,
                                                    f'TM Seller: Ping Error: {self.steamclient.username}')
                        self.ping_alert = True
        except:
            pass

    def ping(self, acc_info, time_sleep):
        username = ''
        while True:
            self.update_account_data_info()
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                self.request_to_ping()
            except:
                Logs.log(f"Error during take session in ping for {username}")
            time.sleep(time_sleep)

    def store_ping(self, acc_info, time_sleep):
        username = ''
        while True:
            self.update_account_data_info()
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                url = f'https://market.csgo.com/api/v2/go-offline?key={self.steamclient.tm_api}'
                response = requests.get(url, timeout=10)
                response_data = response.json()
                if response_data['success'] is not True:
                    Logs.log(f'Restart Store Error')
            except:
                Logs.log(f"Error in store_ping for {username}")
            time.sleep(2)
            self.request_to_ping()
            time.sleep(time_sleep)

    def store_items_visible(self, acc_info, time_sleep):
        search_result = False
        username = ''
        while True:
            if search_result:
                break
            time.sleep(time_sleep)
            self.update_account_data_info()
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                items_url = f'https://market.csgo.com/api/v2/items?key={self.steamclient.tm_api}'
                response = requests.get(items_url, timeout=10)
                response_data = response.json()
                items_on_sale = response_data['items']
                if (items_on_sale is not None
                        and len(items_on_sale) < self.tm_visible_store_num_of_items and len(items_on_sale) != 0):
                    for _ in range(len(items_on_sale)):
                        random_item = random.choice(items_on_sale)
                        if random_item['status'] == '1':
                            hash_name = random_item['market_hash_name']
                            coded_hash_name = urllib.parse.quote(hash_name)
                            item_id = random_item['item_id']
                            another_tm_api = self.search_in_merges_by_username(self.steamclient.username)['tm apikey']
                            search_url = (f'https://market.csgo.com/api/v2/search-list-items-by-hash-name-all?'
                                          f'key={another_tm_api}&extended=1&list_hash_name[]={coded_hash_name}')
                            search_response = requests.get(search_url, timeout=10)
                            search_response_data = search_response.json()

                            search_list = search_response_data['data'][hash_name]

                            for dictionary in search_list:
                                if 'id' in dictionary and str(dictionary['id']) == item_id:
                                    search_result = True
                                    break
                            if not search_result:
                                Logs.log(f'{username}: No active items listed in Store')
                                self.tm_tg_bot.send_message(self.tm_tg_id,
                                                            f'TM Seller: No active items listed in Store: {username}')
                            break
                elif len(items_on_sale) > self.tm_visible_store_num_of_items:
                    Logs.log(f'{username}: Not all items listed in Store')
                    self.tm_tg_bot.send_message(self.tm_tg_id, f'TM Seller: Not all items listed in Store: {username}')
                    break
                else:
                    my_inventory_url = f'https://market.csgo.com/api/v2/my-inventory/?key={self.steamclient.tm_api}'
                    my_inventory_response = requests.get(my_inventory_url, timeout=10)
                    my_inventory_response_data = my_inventory_response.json()
                    my_inventory = my_inventory_response_data['items']
                    tradable_inventory = []
                    for item in my_inventory:
                        if item['tradable'] == 1:
                            tradable_inventory.append(item)
                    if len(tradable_inventory) > 0:
                        Logs.log(f'{username}: No active items listed in Store')
                        self.tm_tg_bot.send_message(self.tm_tg_id,
                                                    f'TM Seller: No active items listed in Store: '
                                                    f'{username}')

            except:
                pass
            time.sleep(30)
        Logs.log(f'{username}: Thread store_items_visible was terminated')


    def validity_tm_apikey(self, time_sleep):
        while True:
            for acc_info in self.content_acc_list:
                try:
                    username = acc_info['username']
                    tm_api_key = acc_info['tm apikey']
                    balance_url = f'https://market.csgo.com/api/v2/get-money?key={tm_api_key}'
                    search_response = requests.get(balance_url, timeout=10)
                    search_response_data = search_response.json()
                    if 'error' in search_response_data and search_response_data['error'] == 'Bad KEY':
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
                response = requests.get(current_balance_url, timeout=10)
                if response.status_code == 200:
                    data = json.loads(response.text)
                    money_value = data["money"]
                    balance_tm = math.floor(money_value)
                    if balance_tm > 0:
                        time.sleep(3)
                        new_value = balance_tm * 100
                        withdrawing_tm_url = (f'https://market.csgo.com/api/v2/money-send/{new_value}/{api_to_withdraw}?'
                                              f'pay_pass=34368&key={tm_api}')
                        response = requests.get(withdrawing_tm_url, timeout=10)
                        if response.status_code == 200:
                            data = json.loads(response.text)
                            if 'amount' in data:
                                withdraw_money = data["amount"] / 100
                                Logs.log(f'{username}: {withdraw_money}: RUB transferred')
                            if 'error' in data and data['error'] == "wrong_payment_password":
                                set_pay_password_url = (f'https://market.csgo.com/api/v2/set-pay-password?'
                                                        f'new_password=34368&key={tm_api}')
                                response = requests.get(set_pay_password_url)
                                if response.status_code == 200:
                                    data = json.loads(response.text)
                                    if 'success' in data and data["success"]:
                                        Logs.log(f'{username}: payment password has been successfully set')
            except:
                pass



