from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.thread_manager import ThreadManager
import time
import requests
import random
import urllib.parse


class TMOnline(ThreadManager):
    def __init__(self):
        super().__init__()
        self.ping_alert = False

    def request_to_ping(self):
        try:
            url_to_ping = f'https://{self.tm_url}/api/v2/ping-new?key={self.steamclient.tm_api}'
            json_data = {
                'access_token': self.steamclient.access_token
            }
            if self.steamclient.proxies and 'http' in self.steamclient.proxies:
                json_data['proxy'] = self.steamclient.proxies['http']
            response = requests.post(url_to_ping, json=json_data, timeout=30).json()
            return response
        except:
            return None

    def ping(self, acc_info, time_sleep):
        username = ''
        while True:
            self.update_account_data_info()
            try:
                self.take_session(acc_info)
                response = self.request_to_ping()
                if (response is not None and 'success' in response and response['success'] is False
                        and 'message' in response and response['message'] != 'too early for ping'):
                    Logs.log(f"{self.steamclient.username}: Ping Error: {response['message']}")
                    if not self.ping_alert:
                        Logs.send_msg_in_tg(self.tm_tg_info, 'Ping Error', self.steamclient.username)
                        self.ping_alert = True
            except:
                Logs.log(f'Error during take session in ping for {username}')
            time.sleep(time_sleep)

    def restart_site_store(self, acc_info, time_sleep):
        username = ''
        while True:
            self.update_account_data_info()
            self.take_session(acc_info)
            url = f'https://{self.tm_url}/api/v2/go-offline?key={self.steamclient.tm_api}'

            try:
                response = requests.get(url, timeout=30).json()
            except:
                response = None
            if response and 'success' in response and response['success'] is not True:
                Logs.log(f'{username}: Offline Store Error')
            time.sleep(2)
            self.request_to_ping()
            time.sleep(time_sleep)

    def store_items_visible(self, acc_info, time_sleep):
        username = ''
        while True:
            time.sleep(time_sleep)
            search_result = False
            self.update_account_data_info()
            try:
                self.take_session(acc_info)
                try:
                    my_inventory_url = f'https://{self.tm_url}/api/v2/my-inventory/?key={self.steamclient.tm_api}'
                    my_inventory_response = requests.get(my_inventory_url, timeout=30).json()
                    my_inventory = my_inventory_response['items']
                except:
                    my_inventory = []
                tradable_inventory = []
                for item in my_inventory:
                    if 'tradable' in item and item['tradable'] == 1:
                        tradable_inventory.append(item)
                if len(tradable_inventory) > self.tm_visible_store_num_of_items:
                    Logs.log_and_send_msg_in_tg(self.tm_tg_info, 'Not all items listed in Store', username)
                    raise ExitException

                items_url = f'https://{self.tm_url}/api/v2/items?key={self.steamclient.tm_api}'
                try:
                    response = requests.get(items_url, timeout=30).json()
                    items_on_sale = response['items']
                except:
                    items_on_sale = None
                if items_on_sale and len(items_on_sale) != 0:
                    for _ in range(len(items_on_sale)):
                        random_item = random.choice(items_on_sale)
                        if random_item['status'] == '1':
                            hash_name = random_item['market_hash_name']
                            coded_hash_name = urllib.parse.quote(hash_name)
                            item_id = random_item['item_id']
                            another_tm_apis_list = self.search_in_merges_by_username(
                                self.steamclient.username)['tm apikey']
                            another_tm_api = random.choice(another_tm_apis_list)
                            search_url = (f'https://{self.tm_url}/api/v2/search-list-items-by-hash-name-all?'
                                          f'key={another_tm_api}&extended=1&list_hash_name[]={coded_hash_name}')
                            try:
                                search_response = requests.get(search_url, timeout=30).json()
                                search_list = search_response['data'][hash_name]
                                for dictionary in search_list:
                                    if 'id' in dictionary and str(dictionary['id']) == str(item_id):
                                        search_result = True
                                        break
                                if not search_result:
                                    Logs.log_and_send_msg_in_tg(self.tm_tg_info, 'Store Visible Error', username)
                                    raise ExitException
                            except ExitException:
                                raise ExitException
                            except:
                                pass
            except ExitException:
                break
            except:
                Logs.log(f'{username}: Store items visible error')
        Logs.log(f'{username}: Thread store_items_visible was terminated')





