import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.sellpy.logs import Logs, ExitException


class TMOnline(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.ping_alert = False
        self.inventory_errors = self.listed_errors = 0

    def ping(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    response = self.request_to_ping()
                    if (response and 'success' in response and 'message' in response
                            and response['message'] != 'too early for ping'):
                        Logs.log(f"Ping: Error to ping: {response['message']}", self.steamclient.username)
                        if not self.ping_alert:
                            Logs.notify(self.tg_info, f"Ping: Error to ping: {response['message']}",
                                        self.steamclient.username)
                            self.ping_alert = True
            except Exception as e:
                Logs.notify_except(self.tg_info, f'Ping Global Error: {e}', self.steamclient.username)
            time.sleep(self.ping_global_time)

    def request_to_ping(self, timeout=30):
        try:
            url_to_ping = f'{self.site_url}/api/v2/ping-new?key={self.tm_apikey}'
            json_data = {
                'access_token': self.steamclient.access_token
            }
            if self.steamclient.proxies and 'http' in self.steamclient.proxies:
                json_data['proxy'] = self.steamclient.proxies['http']
            response = requests.post(url_to_ping, json=json_data, timeout=timeout).json()
            return response
        except:
            return None

    def restart_store(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url = f'{self.site_url}/api/v2/go-offline?key={self.tm_apikey}'
                        response = requests.get(url, timeout=15).json()
                    except:
                        response = None
                    if response and 'success' in response and response['success'] is not True and len(response) == 1:
                        Logs.log(f'Restart Store: Offline request failed', self.steamclient.username)
                    time.sleep(3)
                    self.request_to_ping(timeout=15)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Restart Store Global Error: {e}", self.steamclient.username)
            time.sleep(self.restart_store_global_time)

    # region Visible Store
    def visible_store(self):  # Global Function (class_for_account_functions)
        while True:
            time.sleep(self.visible_store_global_time)
            try:
                if self.active_session:
                    self.visible_store_inventory()
                    self.visible_store_listed()
            except ExitException:
                break
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Visible Store Global Error: {e}", self.steamclient.username)

    def visible_store_inventory(self):
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
            self.inventory_errors += 1
        else:
            self.inventory_errors = 0

        if self.inventory_errors > self.visible_store_max_number_of_errors:
            Logs.notify(self.tg_info, f"Visible Store: {len(tradable_inventory)} items not listed on sale",
                        self.steamclient.username)
            raise ExitException
        time.sleep(3)

    def visible_store_listed(self):
        try:
            items_url = f'{self.site_url}/api/v2/items?key={self.tm_apikey}'
            response = requests.get(items_url, timeout=30).json()
            items_on_sale = response['items']
        except:
            items_on_sale = None

        if items_on_sale and len(items_on_sale) != 0:
            try:
                another_apis_list = self.search_in_merges_by_username(self.steamclient.username)['tm apikey']
            except:
                another_apis_list = None

            if another_apis_list:
                for _ in range(len(items_on_sale)):
                    random_item = random.choice(items_on_sale)
                    if random_item['status'] == '1':
                        hash_name = random_item['market_hash_name']
                        coded_hash_name = urllib.parse.quote(hash_name)
                        item_id = random_item['item_id']
                        another_api = random.choice(another_apis_list)
                        try:
                            search_url = (f'{self.site_url}/api/v2/search-list-items-by-hash-name-all?'
                                          f'key={another_api}&extended=1&list_hash_name[]={coded_hash_name}')
                            search_response = requests.get(search_url, timeout=30).json()
                            search_list = search_response['data'][hash_name]
                        except:
                            search_list = None

                        search_result = False
                        if search_list:
                            for dictionary in search_list:
                                if 'id' in dictionary and str(dictionary['id']) == str(item_id):
                                    search_result = True
                                    break

                            if not search_result:
                                self.listed_errors += 1
                            else:
                                self.listed_errors = 0
                        break
        if self.listed_errors > self.visible_store_max_number_of_errors:
            Logs.notify(self.tg_info, 'Visible Store: Items not visible in store', self.steamclient.username)
            raise ExitException
    # endregion
