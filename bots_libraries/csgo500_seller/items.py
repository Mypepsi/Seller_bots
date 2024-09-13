import time
import requests
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
                    if filtered_inventory and seller_value:
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
                                requests.post(list_items_steam_url, headers=self.csgo500_jwt_apikey,
                                              json=data, timeout=15)
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

    def get_site_price(self, asset_id_in_phases_inventory, seller_value, limits_value):
        try:
            start_sale_time = asset_id_in_phases_inventory['time']
            hash_name = asset_id_in_phases_inventory['market_hash_name']
            rate = self.content_database_settings[
                'DataBaseSettings']['CSGO500_Seller']['CSGO500_Seller_rate']
        except:
            rate = 0
            start_sale_time = hash_name = None
        if start_sale_time and hash_name and rate:
            for condition in seller_value:
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

    # region Change Price
    def change_price(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                self.update_database_info(prices=True, settings=True, csgo500=True)
                if self.active_session and self.content_database_csgo500:
                    listed_items = []
                    page = 1
                    while True:
                        try:
                            items_url = f'{self.site_url}/api/v1/market/listings/deposit/active?appId=730&page={page}'
                            listed = requests.get(items_url, headers=self.csgo500_jwt_apikey, timeout=15).json()
                            for item in listed['data']['listings']:
                                if 'shortStatus' in item and item['shortStatus'] == 'market_listed':
                                    listed_items.append(item)
                            if len(listed['data']['listings']) < 195:
                                raise
                            page += 1
                            time.sleep(1)
                        except:
                            break
                    if listed_items and isinstance(listed_items, list) and len(listed_items) > 0:
                        if listed_items:
                            filtered_items = self.change_price_delete_items(listed_items)
                            seller_value = self.get_information_for_price()
                            if seller_value:
                                items_count = self.change_price_items_count
                                for i in range(0, len(filtered_items), items_count):
                                    items_list = filtered_items[i:i + items_count]
                                    self.change_price_below_opponent(items_list, seller_value, listed_items)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Change Price Global Error: {e}", self.steamclient.username)
            time.sleep(self.change_price_global_time)

    def change_price_delete_items(self, items_on_sale):
        asset_id_to_delete = []
        items_to_delete = []
        asset_id_on_sale = [item['item']["assetId"] for item in items_on_sale]
        tradable_asset_id = list(self.steam_inventory_tradable.keys())
        for assetid in asset_id_on_sale:
            if assetid not in tradable_asset_id:
                asset_id_to_delete.append(assetid)
                for item in items_on_sale:
                    if assetid == item['item']["assetId"]:
                        items_to_delete.append([item["id"]])
                        break
        self.request_delete_items(items_to_delete)
        filtered_items = []
        for item in items_on_sale:
            if 'item' in item and 'assetId' in item['item'] and item['item']['assetId'] not in asset_id_to_delete:
                filtered_items.append(item)
        return filtered_items

    def request_delete_items(self, items_to_delete):
        for i in range(len(items_to_delete)):
            try:
                delete_url = f'{self.site_url}/api/v1/market/listing/cancel'
                requests.post(delete_url, headers=self.csgo500_jwt_apikey, data={"listingId": items_to_delete[i]},
                              timeout=15)
                time.sleep(1)
            except:
                pass

    def request_to_change_price(self, item_id_to_change_price):
        for key, value in item_id_to_change_price.items():
            data = {
                "listingId": key,
                "value": value
                }
            try:
                url_change_price = f'{self.site_url}/api/v1/market/listing/edit-value'
                requests.post(url_change_price, headers=self.csgo500_jwt_apikey, data=data, timeout=15)
            except:
                pass
            time.sleep(51)

    def change_price_below_opponent(self, items_list, seller_value, listed_items):
        my_prices = {}
        items_id_list = [item["id"] for item in items_list]
        for item in range(len(items_list)):
            item_name = items_list[item]['name']
            item_id = items_list[item]['id']
            for el in self.content_database_csgo500['DataBaseCSGO500'].keys():
                if el == item_name:
                    filtered_dict = {
                        item["site_item_id"]: item for item in self.content_database_csgo500['DataBaseCSGO500'][el]
                        if str(item["site_item_id"]) not in str(items_id_list)
                    }
                    item_prices_all = [item["price"] for item in self.content_database_csgo500['DataBaseCSGO500'][el]]
                    item_prices_opponent = [item["price"] for item in filtered_dict.values()]
                    max_site_price = self.get_site_price(
                        self.steam_inventory_phases[items_list[item]['item']["assetId"]], seller_value, 'max')

                    min_site_price = self.get_site_price(
                        self.steam_inventory_phases[items_list[item]['item']["assetId"]], seller_value, 'min')
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
                    for item_ in listed_items:
                        if item_['id'] == item_id:
                            if item_['originalValue'] > my_price:
                                my_price = item_['originalValue']
                            if item_['value'] != my_price:
                                my_prices[items_list[item]["id"]] = my_price
                            break
                    break
        if len(my_prices) > 0:
            self.request_to_change_price(my_prices)
    # endregion
