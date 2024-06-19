from bots_libraries.information.logs import Logs
from bots_libraries.creator.creator_steam import Steam

import time
import requests
import random
import urllib.parse


class TMOnline(Steam):
    def __init__(self):
        super().__init__()

    def request_to_ping(self):
        json_data = {
            'access_token': f"{self.steamclient.access_token}"
        }
        if 'http' in self.steamclient.proxies:
            json_data['proxy'] = self.steamclient.proxies['http']
        url = f"https://market.csgo.com/api/v2/ping-new?key=" + self.steamclient.tm_api
        try:
            response = requests.post(url, json=json_data, timeout=10)
            if response:
                response_data = response.json()
                if response_data['success'] is False and response_data['message'] != 'too early for pong':
                    Logs.log(f"{self.steamclient.username}: Ping Error: {response_data['message']}")
                    self.tm_tg_bot.send_message(self.tm_tg_id,
                                                f'TM Seller: Ping Error: {self.steamclient.username}')
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
            #time.sleep(time_sleep)
            self.update_account_data_info()
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                items_url = f'https://market.csgo.com/api/v2/items?key={self.steamclient.tm_api}'
                response = requests.get(items_url, timeout=10)
                response_data = response.json()
                items_on_sale = response_data['items']
                print(f"{self.steamclient.username}  {items_on_sale}")
                if items_on_sale is not None and len(items_on_sale) > 0:
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
                else:
                    my_inventory_url = f'https://market.csgo.com/api/v2/my-inventory/?key={self.steamclient.tm_api}'
                    my_inventory_response = requests.get(my_inventory_url, timeout=10)
                    my_inventory_response_data = my_inventory_response.json()
                    my_inventory = my_inventory_response_data['items']
                    print(my_inventory)
                    tradable_inventory = []
                    for item in my_inventory:
                        if item['tradable'] == 1:
                            print("сюда")
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
                    print(search_response_data)
                    if 'error' in search_response_data and search_response_data['error'] == 'Bad KEY':
                        Logs.log(f'{username}: TM API key Error')
                        self.tm_tg_bot.send_message(self.tm_tg_id, f'TM Seller: TM API key Error: {username}')
                except:
                    pass
                time.sleep(10)

            Logs.log(f'TM API key: All TM API key checked ({len(self.content_acc_list)} accounts in MongoDB)')
            time.sleep(time_sleep)







