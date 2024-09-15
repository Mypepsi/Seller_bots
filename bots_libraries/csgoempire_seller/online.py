import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.sellpy.logs import Logs, ExitException


class CSGOEmpireOnline(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    def visible_store(self):  # Global Function (class_for_account_functions)
        while True:
            time.sleep(self.visible_store_global_time)
            search_result = False
            try:
                if self.active_session:
                    try:
                        my_inventory_url = f'{self.site_url}/api/v2/trading/user/inventory?update=false'
                        my_inventory_response = requests.get(my_inventory_url, headers=self.csgoempire_headers, timeout=15).json()
                        my_inventory = my_inventory_response['data']
                    except:
                        my_inventory = []
                    tradable_inventory = []
                    for item in my_inventory:
                        if 'tradable' in item and item['tradable'] is True and 'invalid' not in item:
                            tradable_inventory.append(item)
                    if len(tradable_inventory) > self.visible_store_max_number_of_inv_items:
                        Logs.notify(self.tg_info, f"Visible Store: {len(tradable_inventory)} items not listed on sale",
                                    self.steamclient.username)
                        raise ExitException
                    time.sleep(1)
                    try:
                        items_url = f'{self.site_url}/api/v2/trading/user/trades'
                        response = requests.get(items_url, headers=self.csgoempire_headers, timeout=15).json()
                        items_on_sale = []
                        for item in response['data']['deposits']:
                            if 'status_message' in item and item['status_message'] == 'Processing':
                                items_on_sale.append(item)
                    except:
                        items_on_sale = None
                    if items_on_sale and len(items_on_sale) != 0:
                        try:
                            another_apis_list = self.search_in_merges_by_username(
                                self.steamclient.username)['csgoempire apikey']
                        except:
                            another_apis_list = None
                        if another_apis_list:
                            random_item = random.choice(items_on_sale)
                            hash_name = random_item['item']['market_name']
                            coded_hash_name = urllib.parse.quote(hash_name)
                            item_id = random_item['id']
                            another_api = random.choice(another_apis_list)
                            params = {
                                "per_page": 250,
                                "page": 1,
                                "price_max_above": 99999,
                                "delivery_time_long_max": 99999,
                                "search": coded_hash_name
                            }
                            headers = {
                                'Authorization': f'Bearer {another_api}'
                            }
                            try:
                                search_url = f'{self.site_url}/api/v2/trading/items'
                                search_response = requests.get(search_url, params=params, headers=headers, timeout=15).json()
                                search_list = search_response['data']
                            except:
                                search_list = None
                            if search_list:
                                for dictionary in search_list:
                                    if 'id' in dictionary and str(dictionary['id']) == str(item_id):
                                        search_result = True
                                        break
                                if not search_result:
                                    Logs.notify(self.tg_info, 'Visible Store: Items not visible in store',
                                                self.steamclient.username)
                                    break
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Visible Store Global Error: {e}", self.steamclient.username)
