import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.thread_manager import ThreadManager


class TMOnline(ThreadManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.ping_alert = False

    def ping(self, acc_info, global_time):
        while True:
            try:
                self.update_account_data_info()
                active_session = self.take_session(acc_info)
                if active_session:
                    response = self.request_to_ping()
                    if (response is not None and 'success' in response and response['success'] is False
                            and 'message' in response and response['message'] != 'too early for ping'):
                        Logs.log(f"Ping: Error to ping: {response['message']}", self.steamclient.username)
                        if not self.ping_alert:
                            Logs.notify(self.tg_info, f"Ping: Error to ping: {response['message']}",
                                        self.steamclient.username)
                            self.ping_alert = True
            except Exception as e:
                Logs.notify_except(self.tg_info, f'Ping Global Error: {e}', self.steamclient.username)
            time.sleep(global_time)

    def request_to_ping(self):
        try:
            url_to_ping = f'{self.site_url}/api/v2/ping-new?key={self.tm_apikey}'
            json_data = {
                'access_token': self.steamclient.access_token
            }
            if self.steamclient.proxies and 'http' in self.steamclient.proxies:
                json_data['proxy'] = self.steamclient.proxies['http']
            response = requests.post(url_to_ping, json=json_data, timeout=30).json()
            return response
        except:
            return None

    def restart_store(self, acc_info, global_time):
        while True:
            try:
                self.update_account_data_info()
                active_session = self.take_session(acc_info)
                if active_session:
                    try:
                        url = f'{self.site_url}/api/v2/go-offline?key={self.tm_apikey}'
                        response = requests.get(url, timeout=5).json()
                    except:
                        response = None
                    if response and 'success' in response and response['success'] is not True and len(response) == 1:
                        Logs.log(f'Restart Store: Offline request failed', self.steamclient.username)
                    time.sleep(3)
                    self.request_to_ping()
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Restart Store Global Error: {e}", self.steamclient.username)
            time.sleep(global_time)

    def visible_store(self, acc_info, global_time):
        while True:
            time.sleep(global_time)
            try:
                search_result = False
                self.update_account_data_info()
                active_session = self.take_session(acc_info)
                if active_session:
                    try:
                        my_inventory_url = f'{self.site_url}/api/v2/my-inventory/?key={self.tm_apikey}'
                        my_inventory_response = requests.get(my_inventory_url, timeout=30).json()
                        my_inventory = my_inventory_response['items']
                    except:
                        my_inventory = []
                    tradable_inventory = []
                    for item in my_inventory:
                        if 'tradable' in item and item['tradable'] == 1:
                            tradable_inventory.append(item)
                    if len(tradable_inventory) > self.visible_store_max_number_of_inv_items:
                        Logs.notify(self.tg_info, f"Visible Store: {len(tradable_inventory)} items not listed on sale",
                                    self.steamclient.username)
                        raise ExitException
                    time.sleep(3)
                    try:
                        items_url = f'{self.site_url}/api/v2/items?key={self.tm_apikey}'
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
                                try:
                                    another_tm_apis_list = self.search_in_merges_by_username(
                                        self.steamclient.username)['tm apikey']
                                except:
                                    another_tm_apis_list = None
                                if another_tm_apis_list:
                                    another_tm_api = random.choice(another_tm_apis_list)
                                    try:
                                        search_url = (f'{self.site_url}/api/v2/search-list-items-by-hash-name-all?'
                                                      f'key={another_tm_api}&extended=1&list_hash_name[]={coded_hash_name}')
                                        search_response = requests.get(search_url, timeout=30).json()
                                        search_list = search_response['data'][hash_name]
                                    except:
                                        search_list = []
                                    for dictionary in search_list:
                                        if 'id' in dictionary and str(dictionary['id']) == str(item_id):
                                            search_result = True
                                            break
                                    if not search_result:
                                        Logs.notify(self.tg_info, 'Visible Store: Items not visible in store',
                                                    self.steamclient.username)
                                        raise ExitException
            except ExitException:
                break
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Visible Store Global Error: {e}", self.steamclient.username)




