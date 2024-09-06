import time
import requests
import threading
import urllib.parse
from queue import Queue, Empty
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam


class CSGO500Items(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Add To Sale
    def add_to_sale(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    self.update_database_info(prices=True, settings=True)
                    filtered_inventory = self.add_to_sale_inventory()
                    seller_value = self.get_information_for_price()
                    print(filtered_inventory)
                    print(seller_value)
                    if filtered_inventory and seller_value:
                        print(1)
                        for list_of_asset_id in filtered_inventory:
                            data = {
                                "appId": 730,
                                "items": []
                            }
                            for item_dict in list_of_asset_id:
                                asset_id = item_dict['assetId']
                                site_price = self.get_site_price(self.steam_inventory_phases[str(asset_id)],
                                                                 seller_value, 'max')
                                if site_price < item_dict['value']:
                                    site_price = item_dict['value']
                                if site_price is not None and site_price != 0:
                                    data["items"].append({"assetId": str(asset_id), "value": site_price})
                            try:
                                list_items_steam_url = f'{self.site_url}/api/v1/market/deposit'
                                r = requests.post(list_items_steam_url, headers=self.csgo500_jwt_apikey,
                                              json=data, timeout=15)
                                print(r.json())
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
            my_inventory_url = f'{self.site_url}/api/v1/market/inventory?appId=730'
            my_inventory = requests.get(my_inventory_url, headers=self.csgo500_jwt_apikey, timeout=15).json()
            my_inventory_items = my_inventory['data']
            my_inventory_list = [item for item in my_inventory_items if item.get('tradable', False)]
            acc_data_inventory_assets_id = [int(item['asset_id']) for item in self.steam_inventory_tradable.values()]
            filtered_inventory = [
                item for item in my_inventory_list if int(item['assetId']) in acc_data_inventory_assets_id
            ]
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
                'DataBaseSettings']['CSGO500_Seller']['CSGO500_Seller_rate']
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

                                site_price = round(max_price_with_margin_limits * rate)
                            return site_price
        return None
