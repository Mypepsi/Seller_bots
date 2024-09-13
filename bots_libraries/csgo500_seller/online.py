import jwt
import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam import Steam
from bots_libraries.sellpy.logs import Logs, ExitException


class CSGO500Online(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.ping_alert = False

    def ping(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url_to_ping = f'{self.site_url}/api/v1/market/ping'
                        params = {"version": 2}
                        response = requests.post(
                            url_to_ping, headers=self.csgo500_jwt_apikey, data=params, timeout=15).json()
                    except:
                        response = None
                    if (response and 'success' in response and 'message' in response
                            and response['message'] != 'Ping too soon.'):
                        Logs.log(f"Ping: Error to ping: {response['message']}", self.steamclient.username)
                        if not self.ping_alert:
                            Logs.notify(self.tg_info, f"Ping: Error to ping: {response['message']}",
                                        self.steamclient.username)
                            self.ping_alert = True
            except Exception as e:
                Logs.notify_except(self.tg_info, f'Ping Global Error: {e}', self.steamclient.username)
            time.sleep(self.ping_global_time)

    def visible_store(self):  # Global Function (class_for_account_functions)
        while True:
            # time.sleep(self.visible_store_global_time)
            search_result = False
            try:
                if self.active_session:
                    try:
                        my_inventory_url = f'{self.site_url}/api/v1/market/inventory?appId=730'
                        my_inventory_response = requests.get(my_inventory_url, headers=self.csgo500_jwt_apikey,
                                                             timeout=15).json()
                        my_inventory = my_inventory_response['data']
                    except:
                        my_inventory = []
                    tradable_inventory = []
                    for item in my_inventory:
                        if ('tradable' in item and item['tradable'] is True
                                and 'enabled' in item and item['enabled'] is True):
                            tradable_inventory.append(item)
                    if len(tradable_inventory) > self.visible_store_max_number_of_inv_items:
                        Logs.notify(self.tg_info, f"Visible Store: {len(tradable_inventory)} items not listed on sale",
                                    self.steamclient.username)
                        raise ExitException
                    time.sleep(1)
                    try:
                        items_url = f'{self.site_url}/api/v1/market/listings/deposit/active?appId=730&page=1'
                        response = requests.get(items_url, headers=self.csgo500_jwt_apikey, timeout=15).json()
                        items_on_sale = []
                        for item in response['data']['listings']:
                            if 'shortStatus' in item and item['shortStatus'] == 'market_listed':
                                items_on_sale.append(item)
                    except:
                        items_on_sale = None
                    if items_on_sale and len(items_on_sale) != 0:
                        try:
                            another_apis_list = self.search_in_merges_by_username(
                                self.steamclient.username)['csgo500 parse']
                        except:
                            another_apis_list = None
                        if another_apis_list:
                            random_item = random.choice(items_on_sale)
                            hash_name = random_item['name']
                            item_id = random_item['id']
                            another_api = random.choice(another_apis_list)
                            another_jwt_api_key = jwt.encode(
                                {'userId': another_api['user_id']},
                                another_api['apikey'],
                                algorithm="HS256"
                            )
                            another_csgo500_jwt_apikey = {'x-500-auth': another_jwt_api_key}
                            payload = {"pagination": {"limit": 500},
                                       "filters": {"appId": 730},
                                       "search": hash_name}
                            try:
                                search_url = f'{self.site_url}/api/v1/market/shop'
                                search_response = requests.post(search_url, headers=another_csgo500_jwt_apikey,
                                                                json=payload, timeout=15).json()
                                search_list = search_response['data']['listings']
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
