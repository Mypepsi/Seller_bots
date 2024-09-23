import time
import requests
import threading
import urllib.parse
from queue import Queue, Empty
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class ShadowPayItems(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Add To Sale
    def add_to_sale(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    self.update_database_info(prices=True, settings=True)
                    inventory = self.add_to_sale_inventory()
                    max_items_count = 50
                    filtered_inventory = [inventory[i:i + max_items_count] for i in
                                          range(0, len(inventory), max_items_count)]
                    seller_value = self.get_information_for_price()
                    if filtered_inventory and seller_value:
                        for list_of_asset_id in filtered_inventory:
                            data = {"offers": []}
                            for asset_id in list_of_asset_id:
                                site_price = self.get_site_price(self.steam_inventory_phases[str(asset_id)],
                                                                 seller_value, 'max')
                                if site_price is not None and site_price:
                                    data["offers"].append({"id": asset_id, "price": site_price,
                                                          "project": "csgo", "currency": "USD"})

                            try:
                                list_items_steam_url = f'{self.site_url}/api/v2/user/offers'
                                requests.post(list_items_steam_url, json=data, headers={"Token": self.shadowpay_apikey},
                                              timeout=15)
                            except:
                                Logs.notify(self.tg_info,
                                            f"Add To Sale: Failed to list {max_items_count} items on sale",
                                            self.steamclient.username)
                            time.sleep(5)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Add To Sale Global Error: {e}", self.steamclient.username)

            time.sleep(self.add_to_sale_global_time)

    def add_to_sale_inventory(self):
        try:
            my_inventory_url = f'{self.site_url}/api/v2/user/inventory?token={self.shadowpay_apikey}&project=csgo'
            my_inventory = requests.get(my_inventory_url, timeout=15).json()
            my_inventory_items = my_inventory['data']
            my_inventory_list = [int(item['asset_id']) for item in my_inventory_items if 'tradable' in item and
                                 item['tradable'] and 'skip_reason' in item and not item['skip_reason']]

            acc_data_inventory_assets_id = [int(item['asset_id']) for item in
                                            self.steam_inventory_tradable.values()]
            filtered_inventory = [item for item in my_inventory_list if item in acc_data_inventory_assets_id]
            return filtered_inventory
        except:
            return None

    # endregion

    def get_site_price(self, asset_id_in_phases_inventory, seller_value, limits_value):
        try:
            start_sale_time = asset_id_in_phases_inventory['time']
            hash_name = asset_id_in_phases_inventory['market_hash_name']
            commission = self.content_database_settings[
                'DataBaseSettings']['ShadowPay_Seller']['ShadowPay_Seller_commission']
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
                        if hash_name in price and phases_key is not None:
                            site_price = 0
                            max_price = float(price[hash_name]["max_price"])
                            price_range = self.find_matching_key(max_price,
                                                                 condition['days from'][phases_key]['prices'])
                            if price_range is not None:
                                max_price_with_margin = max_price * condition['days from'][phases_key]['prices'][
                                    price_range]
                                max_price_with_margin_limits = (max_price_with_margin * condition['days from'][
                                    phases_key]['limits'][limits_value])

                                site_price = round(max_price_with_margin_limits / commission, 2)
                            return site_price
        return None

    # region Change Price
    def change_price(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    self.update_database_info(prices=True, settings=True)
                    offset = 0
                    listed_items = []

                    while True:
                        try:
                            items_url = (f'{self.site_url}/api/v2/user/offers?token={self.shadowpay_apikey}&project=csgo'
                                         f'&limit=100&offset={offset}&sort_column=price&sort_dir=asc')
                            listed = requests.get(items_url, timeout=15).json()
                            if 'data' not in listed or not isinstance(listed['data'], list):
                                break

                            response_items = listed['data']
                            listed_items.extend(response_items)

                            if len(response_items) < 90:
                                break

                            offset += 100
                            time.sleep(2)
                        except:
                            break

                    if listed_items and isinstance(listed_items, list) and len(listed_items) > 0:
                        items_with_status_one = []
                        for item in listed_items:
                            item_status = item['state']
                            if item_status == 'active':
                                items_with_status_one.append(item)
                        if items_with_status_one:
                            filtered_items = self.change_price_delete_items(items_with_status_one)
                            seller_value = self.get_information_for_price()
                            try:
                                another_apis_list = self.search_in_merges_by_username(self.steamclient.username)['shadowpay apikey']
                            except:
                                another_apis_list = None
                            if another_apis_list and seller_value and filtered_items:
                                items_count = self.change_price_items_count
                                for i in range(0, len(filtered_items), items_count):
                                    items_list = filtered_items[i:i + items_count]
                                    parsed_info = self.threads_parsing_prices(items_list, another_apis_list)
                                    self.change_price_below_opponent(items_list, parsed_info, seller_value)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Change Price Global Error: {e}", self.steamclient.username)
            time.sleep(self.change_price_global_time)

    def change_price_delete_items(self, items_on_sale):
        items_id_to_delete = []
        tradable_asset_id = list(self.steam_inventory_tradable.keys())
        for item in items_on_sale:
            if int(item['asset_id']) not in tradable_asset_id:
                items_id_to_delete.append(item["id"])
        if len(items_id_to_delete) > 0:
            self.request_to_delete_items(items_id_to_delete)
        filtered_items = []
        for item in items_on_sale:
            if 'id' in item and item["id"] not in items_id_to_delete:
                filtered_items.append(item)
        return filtered_items

    def request_to_delete_items(self, items_id_to_delete):
        items_count_in_request = self.change_price_items_count_in_request
        for i in range(0, len(items_id_to_delete), items_count_in_request):
            sublist = items_id_to_delete[i:i + items_count_in_request]
            json_data = {
                "item_ids": sublist
            }
            try:
                url_change_price = f'{self.site_url}/api/v2/user/offers'
                requests.delete(url_change_price, json=json_data, headers={"Token": self.shadowpay_apikey}, timeout=15)
            except:
                pass
            time.sleep(5)

    def change_price_below_opponent(self, items_list, parsed_info, seller_value):
        my_prices = {}
        items_id_list = [item["id"] for item in items_list]
        for item in range(len(items_list)):
            item_name = items_list[item]['steam_item']['steam_market_hash_name']
            for el in parsed_info.keys():
                if el == item_name:
                    filtered_dict = {
                        item["id"]: item for item in parsed_info[el]
                        if str(item["id"]) not in str(items_id_list)
                    }
                    item_prices_all = [item["price"] for item in parsed_info[el]]
                    item_prices_opponent = [item["price"] for item in filtered_dict.values()]
                    max_site_price = self.get_site_price(
                        self.steam_inventory_phases[items_list[item]["asset_id"]], seller_value, 'max')

                    min_site_price = self.get_site_price(
                        self.steam_inventory_phases[items_list[item]["asset_id"]], seller_value, 'min')
                    if len(item_prices_opponent) > 0 and min_site_price and max_site_price:
                        lower_market_price_opponent = min([float(price) for price in item_prices_opponent])
                        min_price_opponent = (lower_market_price_opponent - 0.01)

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
                                                  f"{self.steam_inventory_phases[items_list[item]['asset_id']]} assetID",
                                    self.steamclient.username)
                        break

                    if items_list[item]['price'] != my_price:
                        my_prices[items_list[item]["id"]] = my_price
                    break
        if len(my_prices) > 0:
            self.request_to_change_price(my_prices)

    def request_to_change_price(self, item_id_to_change_price):
        items_count_in_request = self.change_price_items_count_in_request
        for i in range(0, len(item_id_to_change_price), items_count_in_request):
            sublist_keys = list(item_id_to_change_price.keys())[i:i + items_count_in_request]
            sublist = {k: item_id_to_change_price[k] for k in sublist_keys}
            json_data = {
                "offers": []
            }
            for key, value in sublist.items():
                json_data['offers'].append(
                    {"id": key, "price": value, "currency": "USD"})
            try:
                url_change_price = f'{self.site_url}/api/v2/user/offers'
                requests.patch(url_change_price, json=json_data, headers={"Token": self.shadowpay_apikey}, timeout=15)
            except:
                pass
            time.sleep(5)

    # region Parsing Info for change price
    def threads_parsing_prices(self, items, api_keys):
        threads = {}
        results = {}
        results_lock = threading.Lock()
        hash_queue = Queue()
        unique_items = []
        seen = set()
        for item in items:
            item_name = item['steam_item']['steam_market_hash_name']
            if item_name not in seen:
                unique_items.append(item)
                seen.add(item_name)
        for hash_name in unique_items:
            coded_item_name = urllib.parse.quote(hash_name['steam_item']['steam_market_hash_name'])
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
            offset = 0
            info_to_write = {}
            while True:
                try:
                    list_hash_names = '&steam_market_hash_name[]=' + '&steam_market_hash_name[]='.join(hash_names)
                    search_hash_name_url = (f'https://api.shadowpay.com/api/v2/user/items?token={self.shadowpay_apikey}'
                                            f'&project=csgo&limit=10000&offset={offset}&sort_column=price'
                                            f'&sort_dir=asc{list_hash_names}')
                    parsed_info = requests.get(search_hash_name_url, timeout=15).json()
                    if parsed_info['status'] == 'success' and len(parsed_info['data']) > 0:
                        for item in parsed_info['data']:
                            name = item['steam_item']['steam_market_hash_name']
                            if name not in info_to_write:
                                info_to_write[name] = []
                            info_to_write[name].append(item)
                    if len(parsed_info["data"]) > 9900:
                        offset += 10000
                        time.sleep(1)
                    else:
                        break
                except:
                    break
                if info_to_write:
                    with results_lock:
                        results.update(info_to_write)
        except:
            pass
        finally:
            time.sleep(1)
            del threads[api_key]
    # endregion

    # endregion
