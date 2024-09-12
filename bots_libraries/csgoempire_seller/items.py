import time
import requests
import threading
import urllib.parse
from queue import Queue, Empty
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam


class CSGOEmpireItems(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Add To Sale
    def add_to_sale(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                self.update_database_info(prices=True, settings=True, csgoempire=True)
                if self.active_session and self.content_database_csgoempire:
                    raw_filtered_inventory = self.add_to_sale_inventory()
                    max_items_count = 20
                    filtered_inventory = [raw_filtered_inventory[i:i + max_items_count]
                                          for i in range(0, len(raw_filtered_inventory), max_items_count)]
                    seller_value = self.get_information_for_price()
                    if filtered_inventory and seller_value:
                        for items_list in filtered_inventory:
                            my_prices = self.prices_below_opponent(items_list, seller_value, True)
                            for item in items_list:
                                for key, value in my_prices.items():
                                    if str(item['id']) == str(key):
                                        if 'market_value' in item and item['market_value'] > value:
                                            my_prices[key] = item['market_value']
                                            break
                            data = [{"id": int(key), "coin_value": value} for key, value in my_prices.items()]
                            headers = {
                                "accept": "application/json",
                                "content-type": "application/json",
                                "Authorization": f"Bearer {self.csgoempire_apikey}"
                            }
                            try:
                                list_items_steam_url = f'{self.site_url}/api/v2/trading/deposit'
                                requests.post(list_items_steam_url, json={"items": data}, headers=headers, timeout=15)
                            except:
                                pass
                            time.sleep(5)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Add To Sale Global Error: {e}", self.steamclient.username)

            time.sleep(self.add_to_sale_global_time)

    def add_to_sale_inventory(self):
        try:
            my_inventory_url = f'{self.site_url}/api/v2/trading/user/inventory?update=true'
            my_inventory_response = requests.get(my_inventory_url, headers=self.csgoempire_headers, timeout=15).json()
            my_inventory_items = my_inventory_response['data']
        except:
            my_inventory_items = None
        time.sleep(1)
        try:
            if not my_inventory_items:
                my_inventory_url = f'{self.site_url}/api/v2/trading/user/inventory?update=false'
                my_inventory_response = requests.get(my_inventory_url, headers=self.csgoempire_headers, timeout=15).json()
                my_inventory_items = my_inventory_response['data']

            tradable_inventory = []
            for item in my_inventory_items:
                if 'tradable' in item and item['tradable'] is True and 'invalid' not in item:
                    tradable_inventory.append(item)
            acc_data_inventory_assets_id = [int(item['asset_id']) for item in self.steam_inventory_tradable.values()]
            filtered_inventory = [item for item in tradable_inventory if item['asset_id'] in acc_data_inventory_assets_id]
            return filtered_inventory
        except:
            return None

    # endregion

    def prices_below_opponent(self, items_list, seller_value, add_to_sale_key: bool):
        my_prices = {}
        items_id_list = [item["id"] for item in items_list]
        for item in range(len(items_list)):
            if add_to_sale_key:
                item_name = items_list[item]['market_name']
            else:
                item_name = items_list[item]['item']['market_name']
            parsed_info = self.content_database_csgoempire['DataBaseCSGOEmpire']
            for el in parsed_info.keys():
                if el == item_name:
                    filtered_dict = {
                        item["site_item_id"]: item for item in parsed_info[el]
                        if str(item["site_item_id"]) not in str(items_id_list)
                    }
                    item_prices_all = [item["price"] for item in parsed_info[el]]
                    item_prices_opponent = [item["price"] for item in filtered_dict.values()]
                    if add_to_sale_key:
                        asset_id = str(items_list[item]['asset_id'])
                    else:
                        asset_id = str(items_list[item]['item']['asset_id'])

                    max_site_price = self.get_site_price(
                        self.steam_inventory_phases[asset_id], seller_value, 'max')

                    min_site_price = self.get_site_price(
                        self.steam_inventory_phases[asset_id], seller_value, 'min')

                    if len(item_prices_opponent) > 0 and min_site_price and max_site_price:
                        lower_market_price_opponent = min([int(price) for price in item_prices_opponent])
                        min_price_opponent = (lower_market_price_opponent - 1)

                        if min_site_price <= min_price_opponent <= max_site_price:
                            my_price = min_price_opponent
                        elif min_price_opponent < min_site_price:
                            my_price = min_site_price
                        else:
                            my_price = max_site_price
                    elif len(item_prices_opponent) == 0 and len(item_prices_all) > 0 and max_site_price:
                        my_price = max_site_price
                    else:
                        Logs.notify(self.tg_info, f"Change Price: "
                                                  f"Unable to calculate new price for item on sale: "
                                                  f"{self.steam_inventory_phases[items_list[item]['assetid']]} assetID",
                                    self.steamclient.username)
                        break
                    my_prices[str(items_list[item]["id"])] = my_price
                    break
        return my_prices

    def get_site_price(self, asset_id_in_phases_inventory, conditions, limits_value):
        try:
            start_sale_time = asset_id_in_phases_inventory['time']
            hash_name = asset_id_in_phases_inventory['market_hash_name']
            rate = self.content_database_settings['DataBaseSettings']['CSGOEmpire_Seller']['CSGOEmpire_Seller_rate']
        except:
            rate = 0
            start_sale_time = hash_name = None
        if start_sale_time and hash_name and rate:
            for condition in conditions:
                if condition['date to'] >= start_sale_time >= condition['date from']:
                    current_timestamp = int(time.time())
                    phases_difference = (current_timestamp - start_sale_time) / 86400
                    phases_key = self.find_matching_key(phases_difference, condition['days from'])
                    all_prices = self.content_database_prices['DataBasePrices']
                    for price in all_prices:
                        if hash_name in price and phases_key:
                            site_price = 0
                            max_price = float(price[hash_name]["max_price"])
                            price_range = self.find_matching_key(max_price,
                                                                 condition['days from'][phases_key]['prices'])
                            if price_range:
                                max_price_with_margin = max_price * condition['days from'][phases_key]['prices'][
                                    price_range]
                                max_price_with_margin_limits = (max_price_with_margin * condition['days from'][
                                    phases_key]['limits'][limits_value])

                                site_price = round(max_price_with_margin_limits * 100 * rate)
                            return site_price
        return None

    # region Change Price
    def change_price(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                self.update_database_info(prices=True, settings=True, csgoempire=True)
                if self.active_session and self.content_database_csgoempire:
                    try:
                        items_url = f'{self.site_url}/api/v2/trading/user/trades'
                        listed = requests.get(items_url, headers=self.csgoempire_headers, timeout=15).json()
                        listed_items = listed['data']['deposits']
                    except:
                        listed_items = None
                    if listed_items and isinstance(listed_items, list) and len(listed_items) > 0:
                        items_with_normal_status = []
                        for item in listed_items:
                            if 'status_message' in item and item['status_message'] == 'Processing':
                                items_with_normal_status.append(item)
                        if items_with_normal_status:
                            items_list = self.change_price_delete_items(items_with_normal_status)
                            seller_value = self.get_information_for_price()
                            if seller_value:
                                my_prices = self.prices_below_opponent(items_list, seller_value, False)  # format items_list
                                for item in items_list:
                                    for key, value in my_prices.items():
                                        if str(item['id']) == str(key):
                                            old_price = item['item']['market_value']
                                            suggested_price = None
                                            if 'suggested_price' in item and isinstance(item['suggested_price'], (int, float)):
                                                suggested_price = round(item['suggested_price'] / 1.06, 2) - 0.01
                                            if ((value - 0.01 <= old_price <= value + 0.01)
                                                    or (suggested_price and old_price >= suggested_price)):
                                                del my_prices[key]
                                            break
                                # if len(my_prices) > 0:
                                #     my_prices_to_delete = [int(key) for key in my_prices.keys()]
                                #     self.request_delete_items(my_prices_to_delete)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Change Price Global Error: {e}", self.steamclient.username)
            time.sleep(self.change_price_global_time)

    def change_price_delete_items(self, items_on_sale):
        items_id_to_delete = []
        tradable_asset_id = list(self.steam_inventory_tradable.keys())
        for item in items_on_sale:
            if item['item']['asset_id'] not in tradable_asset_id:
                items_id_to_delete.append(item["id"])
        if len(items_id_to_delete) > 0:
            self.request_delete_items(items_id_to_delete)
        filtered_items = []
        for item in items_on_sale:
            if 'id' in item and item["id"] not in items_id_to_delete:
                filtered_items.append(item)
        return filtered_items

    def request_delete_items(self, items_id_to_delete):
        items_to_change_price = 50
        for i in range(0, len(items_id_to_delete), items_to_change_price):
            sublist = items_id_to_delete[i:i + items_to_change_price]
            data = {
                "ids": sublist
            }
            try:
                url_change_price = f'{self.site_url}/api/v2/trading/deposit/cancel'
                requests.post(url_change_price, data=data, timeout=15)
            except:
                pass
            time.sleep(5)


    # endregion

