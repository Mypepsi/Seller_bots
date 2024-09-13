import time
import requests
import threading
import urllib.parse
from queue import Queue, Empty
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam


class WaxpeerItems(Steam):
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
                            data = {"items": []}
                            for asset_id in list_of_asset_id:
                                site_price = self.get_site_price(self.steam_inventory_phases[str(asset_id)],
                                                                 seller_value, 'max')
                                if site_price is not None and site_price != 0:
                                    data["items"].append({"item_id": asset_id, "price": site_price})
                            try:
                                list_items_steam_url = f'{self.site_url}/v1/list-items-steam?api={self.waxpeer_apikey}'
                                requests.post(list_items_steam_url, json=data, timeout=15)
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
            update_inventory_url = f'{self.site_url}/v1/fetch-my-inventory?api={self.waxpeer_apikey}'
            requests.get(update_inventory_url, timeout=15)
        except:
            pass
        time.sleep(10)
        try:
            my_inventory_url = f'{self.site_url}/v1/get-my-inventory?api={self.waxpeer_apikey}&game=730'
            my_inventory = requests.get(my_inventory_url, timeout=15).json()
            my_inventory_items = my_inventory['items']
            my_inventory_list = [item['item_id'] for item in my_inventory_items]
            acc_data_inventory_assets_id = [int(item['asset_id']) for item in self.steam_inventory_tradable.values()]
            filtered_inventory = [item for item in my_inventory_list if item in acc_data_inventory_assets_id]
            chunk = 100
            return [filtered_inventory[i:i + chunk] for i in range(0, len(filtered_inventory), chunk)]
        except:
            return None

    # endregion

    def get_site_price(self, asset_id_in_phases_inventory, seller_value, limits_value):
        try:
            start_sale_time = asset_id_in_phases_inventory['time']
            hash_name = asset_id_in_phases_inventory['market_hash_name']
            commission = self.content_database_settings[
                'DataBaseSettings']['Waxpeer_Seller']['Waxpeer_Seller_commission']
        except:
            commission = 0
            start_sale_time = hash_name = None
        if start_sale_time and hash_name and commission:
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

                                site_price = round(max_price_with_margin_limits * 1000 / commission)
                            return site_price
        return None

    # region Change Price
    def change_price(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    self.update_database_info(prices=True, settings=True)
                    try:
                        items_url = f'{self.site_url}/v1/list-items-steam?api={self.waxpeer_apikey}'
                        listed = requests.get(items_url, timeout=15).json()
                        listed_items = listed['items']
                    except:
                        listed_items = None
                    if listed_items and isinstance(listed_items, list) and len(listed_items) > 0:
                        filtered_items = self.change_price_delete_items(listed_items)
                        seller_value = self.get_information_for_price()
                        try:
                            another_apis_list = self.search_in_merges_by_username(self.steamclient.username)[
                                'waxpeer apikey']
                        except:
                            another_apis_list = None
                        if another_apis_list and seller_value and filtered_items:
                            items_count = self.change_price_items_count
                            for i in range(0, len(filtered_items), items_count):
                                items_list = filtered_items[i:i + items_count]
                                parsed_info = self.threads_parsing_prices(items_list, another_apis_list)
                                self.change_price_below_opponent(items_list, parsed_info, seller_value, listed_items)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Change Price Global Error: {e}", self.steamclient.username)
            time.sleep(self.change_price_global_time)

    def change_price_delete_items(self, items_on_sale):
        item_id_to_delete = []
        item_id_on_sale = [item["item_id"] for item in items_on_sale]
        tradable_asset_id = list(self.steam_inventory_tradable.keys())
        for assetid in item_id_on_sale:
            if assetid not in tradable_asset_id:
                item_id_to_delete.append({"item_id": assetid, "price": 0})
        self.request_to_change_price(item_id_to_delete)
        filtered_items = []
        for item in items_on_sale:
            if 'item_id' in item and not any(d["item_id"] == item["item_id"] for d in item_id_to_delete):
                filtered_items.append(item)
        return items_on_sale

    def request_to_change_price(self, item_id_to_change_price):
        items_count_in_request = self.change_price_items_count_in_request
        data = []
        if isinstance(item_id_to_change_price, list):
            sublist = [item_id_to_change_price[i:i + items_count_in_request]
                       for i in range(0, len(item_id_to_change_price), items_count_in_request)]
            for i in sublist:
                data.append({"items": i})
        elif isinstance(item_id_to_change_price, dict):
            for i in range(0, len(item_id_to_change_price), items_count_in_request):
                sublist_keys = list(item_id_to_change_price.keys())[i:i + items_count_in_request]
                sublist = {k: item_id_to_change_price[k] for k in sublist_keys}
                items = {ui_id: item_id_to_change_price[ui_id] for ui_id in sublist}
                data.append({
                    "items": [{"item_id": key, "price": value} for key, value in items.items()]
                })
        for info in data:
            try:
                url_change_price = f'{self.site_url}/v1/edit-items?api={self.waxpeer_apikey}'
                r = requests.post(url_change_price, json=info, timeout=15)
            except:
                pass
            time.sleep(5)

    def change_price_below_opponent(self, items_list, parsed_info, seller_value, listed_items):
        my_prices = {}
        items_id_list = [item["item_id"] for item in items_list]
        for item in range(len(items_list)):
            item_name = items_list[item]['name']
            item_id = items_list[item]['item_id']
            for el in parsed_info.keys():
                if el == item_name:
                    filtered_dict = {
                        item["item_id"]: item for item in parsed_info[el]
                        if str(item["item_id"]) not in str(items_id_list)
                    }
                    item_prices_all = [item["price"] for item in parsed_info[el]]
                    item_prices_opponent = [item["price"] for item in filtered_dict.values()]
                    max_site_price = self.get_site_price(
                        self.steam_inventory_phases[str(items_list[item]["item_id"])], seller_value, 'max')

                    min_site_price = self.get_site_price(
                        self.steam_inventory_phases[str(items_list[item]["item_id"])], seller_value, 'min')

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
                        if item_['item_id'] == item_id and item_['price'] != my_price:
                            my_prices[items_list[item]["item_id"]] = my_price
                            break
                    break
        if len(my_prices) > 0:
            self.request_to_change_price(my_prices)

    # region Parsing Info for change price
    def threads_parsing_prices(self, items, api_keys):
        threads = {}
        results = {}
        results_lock = threading.Lock()
        hash_queue = Queue()
        unique_items = []
        seen = set()
        for item in items:
            item_name = item['name']
            if item_name not in seen:
                unique_items.append(item)
                seen.add(item_name)
        for hash_name in unique_items:
            coded_item_name = urllib.parse.quote(hash_name['name'])
            hash_queue.put(coded_item_name)
        while not hash_queue.empty():
            for api_key in api_keys:
                if api_key not in threads and not hash_queue.empty():
                    hash_names = []
                    items_for_parse = 50
                    for _ in range(min(items_for_parse, hash_queue.qsize())):
                        try:
                            hash_names.append(hash_queue.get_nowait())
                        except Empty:
                            break
                    thread = threading.Thread(target=self.request_to_parsing_prices,
                                              args=(api_key, hash_names, results, results_lock, threads))
                    thread.start()
                    threads[api_key] = thread
            time.sleep(1)
        while True:
            if len(threads) == 0:
                break
            time.sleep(1)
        return results

    def request_to_parsing_prices(self, api_key, hash_names, results, results_lock, threads):
        try:
            list_hash_names = '&names=' + '&names='.join(hash_names)
            search_hash_name_url = f'{self.site_url}/v1/search-items-by-name?api={api_key}{list_hash_names}'
            parsed_info = requests.get(search_hash_name_url, timeout=15).json()
            if parsed_info['success'] and len(parsed_info['items']) > 0:
                info_to_write = {}
                for item in parsed_info['items']:
                    name = item['name']
                    if name not in info_to_write:
                        info_to_write[name] = []
                    info_to_write[name].append(item)
                with results_lock:
                    results.update(info_to_write)
        except:
            pass
        time.sleep(1)
        del threads[api_key]

    # endregion

    # endregion
