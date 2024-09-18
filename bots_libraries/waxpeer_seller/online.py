import time
import random
import requests
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.sellpy.logs import Logs, ExitException


class WaxpeerOnline(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.ping_alert = False
        self.inventory_errors = self.listed_errors = 0

    def ping(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url_to_ping = (f'{self.site_url}/v1/check-wss-user?'
                                       f'api=1{self.waxpeer_apikey}&'
                                       f'steamid={self.steamclient.steam_guard["steamid"]}')
                        response = requests.get(url_to_ping, timeout=15).json()
                    except:
                        response = None
                    if response and 'success' in response and 'msg' in response and response['msg'] != 'wrong api':
                        Logs.log(f"Ping: Error to ping: {response['msg']}", self.steamclient.username)
                        if not self.ping_alert:
                            Logs.notify(self.tg_info, f"Ping: Error to ping: {response['msg']}",
                                        self.steamclient.username)
                            self.ping_alert = True
            except Exception as e:
                Logs.notify_except(self.tg_info, f'Ping Global Error: {e}', self.steamclient.username)
            time.sleep(self.ping_global_time)

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
            my_inventory_url = f'{self.site_url}/v1/get-my-inventory?api={self.waxpeer_apikey}&game=730'
            my_inventory_response = requests.get(my_inventory_url, timeout=15).json()
            my_inventory = my_inventory_response['items']
        except:
            my_inventory = []

        if len(my_inventory) > self.visible_store_max_number_of_inv_items:
            self.inventory_errors += 1
        else:
            self.inventory_errors = 0

        if self.inventory_errors > self.visible_store_max_number_of_errors:
            Logs.notify(self.tg_info, f"Visible Store: {len(my_inventory)} items not listed on sale",
                        self.steamclient.username)
            raise ExitException
        time.sleep(1)

    def visible_store_listed(self):
        try:
            items_url = f'{self.site_url}/v1/list-items-steam?api={self.waxpeer_apikey}'
            response = requests.get(items_url, timeout=15).json()
            items_on_sale = response['items']
        except:
            items_on_sale = None

        if items_on_sale and len(items_on_sale) != 0:
            try:
                another_apis_list = self.search_in_merges_by_username(self.steamclient.username)['waxpeer apikey']
            except:
                another_apis_list = None

            if another_apis_list:
                random_item = random.choice(items_on_sale)
                item_id = random_item['item_id']
                another_api = random.choice(another_apis_list)

                try:
                    search_url = (f'{self.site_url}/v1/check-availability?'
                                  f'api={another_api}&item_id={item_id}')
                    search_response = requests.get(search_url, timeout=15).json()
                    search_list = search_response['items']
                except:
                    search_list = None

                search_result = False
                if search_list:
                    for item in search_list:
                        if str(item['item_id']) == str(item_id):
                            search_result = True
                            break

                if not search_result:
                    self.listed_errors += 1
                else:
                    self.listed_errors = 0

        if self.listed_errors > self.visible_store_max_number_of_errors:
            Logs.notify(self.tg_info, 'Visible Store: Items not visible in store', self.steamclient.username)
            raise ExitException

    # endregion