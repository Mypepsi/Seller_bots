import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.sellpy.logs import Logs, ExitException


class ShadowPayOnline(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.inventory_errors = self.listed_errors = 0

    # region Visible Store
    def visible_store(self):  # Global Function (class_for_account_functions)
        while True:
            time.sleep(self.visible_store_global_time)
            try:
                if self.active_session:
                    self.visible_store_inventory()
                    self.visible_store_listed()
                print(f'{self.inventory_errors} = {self.listed_errors}')
            except ExitException:
                break
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Visible Store Global Error: {e}", self.steamclient.username)

    def visible_store_inventory(self):
        try:
            my_inventory_url = f'{self.site_url}/api/v2/user/inventory?token={self.shadowpay_apikey}&project=csgo'
            my_inventory_response = requests.get(my_inventory_url, timeout=15).json()
            my_inventory = my_inventory_response['data']
        except:
            my_inventory = []

        tradable_inventory = []
        for item in my_inventory:
            if ('tradable' in item and item['tradable'] == 1
                    and 'skip_reason' in item and item['skip_reason'] is not None):
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
            items_url = (f'{self.site_url}/api/v2/user/offers?token={self.shadowpay_apikey}'
                         f'&project=csgo&limit=100&offset=0&sort_column=price&sort_dir=asc')
            response = requests.get(items_url, timeout=15).json()
            items_on_sale = response['data']
        except:
            items_on_sale = None

        if items_on_sale and len(items_on_sale) != 0:
            try:
                another_apis_list = self.search_in_merges_by_username(self.steamclient.username)['shadowpay apikey']
            except:
                another_apis_list = None

            if another_apis_list:
                for _ in range(len(items_on_sale)):
                    random_item = random.choice(items_on_sale)
                    if random_item['state'] == 'active':
                        hash_name = random_item['steam_item']['steam_market_hash_name']
                        coded_hash_name = urllib.parse.quote(hash_name)
                        item_id = random_item['id']
                        another_api = random.choice(another_apis_list)
                        try:
                            search_url = (f'{self.site_url}/api/v2/user/items?token={another_api}'
                                          f'&project=csgo&limit=1000&offset=0&sort_column=price&sort_dir=asc'
                                          f'&steam_market_hash_name={coded_hash_name}')
                            search_response = requests.get(search_url, timeout=15).json()
                            search_list = search_response['data']
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
