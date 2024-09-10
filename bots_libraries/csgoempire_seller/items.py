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
                if self.active_session:
                    self.update_database_info(prices=True, settings=True, csgoempire=True)
                    filtered_inventory = self.add_to_sale_inventory()
                    seller_value = self.get_information_for_price()
                    if filtered_inventory and seller_value:
                        for list_of_asset_id in filtered_inventory:
                            my_prices = self.prices_below_opponent(list_of_asset_id, seller_value)
                            for item in list_of_asset_id:
                                for key, value in my_prices.items():
                                    if str(item['id']) == str(key):
                                        if item['market_value'] > value:
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
                                Logs.notify(self.tg_info,
                                            f"Add To Sale: Failed to add item on sale: {data} assetID`s",
                                            self.steamclient.username)
                            time.sleep(5)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Add To Sale Global Error: {e}", self.steamclient.username)

            time.sleep(self.add_to_sale_global_time)

    def add_to_sale_inventory(self):
        try:
            my_inventory_url = f'{self.site_url}/api/v2/trading/user/inventory'
            my_inventory_response = requests.get(my_inventory_url, headers=self.csgoempire_headers, timeout=15).json()
            my_inventory_items = my_inventory_response['data']
        except:
            my_inventory_items = None
        time.sleep(10)
        try:
            if not my_inventory_items:
                my_inventory_url = f'{self.site_url}/api/v2/trading/user/inventory?update=false'
                my_inventory_response = requests.get(my_inventory_url, headers=self.csgoempire_headers, timeout=15).json()
                my_inventory_items = my_inventory_response['data']

            tradable_inventory = []
            for item in my_inventory_items:
                if 'tradable' in item and item['tradable'] is True and 'invalid' not in item:
                    tradable_inventory.append(item)
            my_inventory_list = [item['id'] for item in tradable_inventory]
            acc_data_inventory_assets_id = [int(item['asset_id']) for item in self.steam_inventory_tradable.values()]
            filtered_inventory = [item for item in my_inventory_items if item['asset_id'] in acc_data_inventory_assets_id]
            chunk = 20
            return [filtered_inventory[i:i + chunk] for i in range(0, len(filtered_inventory), chunk)]
        except:
            return None

    # endregion

    def get_site_price(self, asset_id_in_phases_inventory, conditions, limits_value):
        try:
            start_sale_time = asset_id_in_phases_inventory['time']
            hash_name = asset_id_in_phases_inventory['market_hash_name']
            rate = self.content_database_settings[
                'DataBaseSettings']['CSGOEmpire_Seller']['CSGOEmpire_Seller_rate']
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

    def prices_below_opponent(self, items_list, seller_value):
        my_prices = {}
        items_id_list = [item["id"] for item in items_list]
        for item in range(len(items_list)):
            item_name = items_list[item]['market_name']
            parsed_info = self.content_database_csgoempire['DataBaseCSGOEmpire']
            for el in parsed_info.keys():
                if el == item_name:
                    filtered_dict = {
                        item["site_item_id"]: item for item in parsed_info[el]
                        if str(item["site_item_id"]) not in str(items_id_list)
                    }
                    item_prices_all = [item["price"] for item in parsed_info[el]]
                    item_prices_opponent = [item["price"] for item in filtered_dict.values()]
                    max_site_price = self.get_site_price(
                        self.steam_inventory_phases[str(items_list[item]["asset_id"])], seller_value, 'max')

                    min_site_price = self.get_site_price(
                        self.steam_inventory_phases[str(items_list[item]["asset_id"])], seller_value, 'min')

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

