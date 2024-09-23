import time
import requests
import threading
import urllib.parse
from queue import Queue, Empty
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class BuffItems(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Add To Sale
    def add_to_sale(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    self.update_database_info(prices=True, settings=True)
                    inventory = self.add_to_sale_inventory()
                    max_items_count = 100
                    filtered_inventory = [inventory[i:i + max_items_count] for i in range(0, len(inventory), max_items_count)]
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
                                            f"Add To Sale: Failed to list {max_items_count} items on sale",
                                            self.steamclient.username)
                            time.sleep(5)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Add To Sale Global Error: {e}", self.steamclient.username)

            time.sleep(self.add_to_sale_global_time)

    def add_to_sale_inventory(self):
        try:
            my_inventory_url = (f'{self.site_url}/api/market/steam_inventory?game=csgo&force=1&page_num={page}&'
                                f'page_size=500&search=&state=tradable&sort_by=price.desc&_={int(time.time() * 1000)}')
            my_inventory = requests.get(my_inventory_url, timeout=15).json()
            my_inventory_items = my_inventory['!!! items !!!']
            my_inventory_list = [item['!!! item_id !!!'] for item in my_inventory_items if item["state_toast"] is None
                                 and item["progress_text"] == 'Idle' and item["state_text"] == 'Tradable']
            acc_data_inventory_assets_id = [int(item['!!! asset_id !!!']) for item in self.steam_inventory_tradable.values()]
            filtered_inventory = [item for item in my_inventory_list if item in acc_data_inventory_assets_id]
            return filtered_inventory
        except:
            return None

    # endregion

    def get_site_price(self, asset_id_in_phases_inventory, seller_value, limits_value):
        try:
            start_sale_time = asset_id_in_phases_inventory['time']
            hash_name = asset_id_in_phases_inventory['market_hash_name']
            commission = self.content_database_settings['DataBaseSettings']['Buff_Seller']['Buff_Seller_commission']
            rate = self.content_database_settings['DataBaseSettings']['Buff_Seller']['Buff_Seller_rate']
        except:
            rate = commission = 0
            start_sale_time = hash_name = None
        if start_sale_time and hash_name and commission and rate:
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
                                max_price_with_margin = max_price * condition['days from'][phases_key]['prices'][price_range]
                                max_price_with_margin_limits = (max_price_with_margin * condition[
                                    'days from'][phases_key]['limits'][limits_value])

                                site_price = round(max_price_with_margin_limits * rate / commission)
                            return site_price
        return None

    # region Change Price
    def change_price(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    self.update_database_info(prices=True, settings=True)
                    try:
                        items_url = f'{self.site_url}/api/v2/items?key={self.tm_apikey}'
                        listed = requests.get(items_url, timeout=15).json()
                        listed_items = listed['items']
                    except:
                        listed_items = None
                    if listed_items and isinstance(listed_items, list) and len(listed_items) > 0:
                        items_with_status_one = []
                        for item in listed_items:
                            item_status = item['status']
                            if item_status == '1':
                                items_with_status_one.append(item)
                        if items_with_status_one:
                            filtered_items = self.change_price_delete_items(items_with_status_one)
                            seller_value = self.get_information_for_price()
                            try:
                                another_apis_list = self.search_in_merges_by_username(self.steamclient.username)['tm apikey']
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
        items_id_to_delete = {}
        tradable_asset_id = list(self.steam_inventory_tradable.keys())
        for item in items_on_sale:
            if item['assetid'] not in tradable_asset_id:
                items_id_to_delete[item["item_id"]] = 0
        if len(items_id_to_delete) > 0:
            self.request_to_change_price(items_id_to_delete)
        filtered_items = []
        for item in items_on_sale:
            if 'item_id' in item and item["item_id"] not in items_id_to_delete:
                filtered_items.append(item)
        return filtered_items

    def request_to_change_price(self, item_id_to_change_price):
        items_count_in_request = self.change_price_items_count_in_request
        for i in range(0, len(item_id_to_change_price), items_count_in_request):
            sublist_keys = list(item_id_to_change_price.keys())[i:i + items_count_in_request]
            sublist = {k: item_id_to_change_price[k] for k in sublist_keys}
            items = {ui_id: item_id_to_change_price[ui_id] for ui_id in sublist}
            data = {f'list[{ui_id}]': price for ui_id, price in items.items()}
            try:
                url_change_price = f'{self.site_url}/api/MassSetPriceById/?key={self.tm_apikey}'
                requests.post(url_change_price, data=data, timeout=15)
            except:
                pass
            time.sleep(60)

    def change_price_below_opponent(self, items_list, parsed_info, seller_value, listed_items):
        my_prices = {}
        items_id_list = [item["item_id"] for item in items_list]
        for item in range(len(items_list)):
            item_name = items_list[item]['market_hash_name']
            item_id = items_list[item]['item_id']
            for el in parsed_info.keys():
                if el == item_name:
                    filtered_dict = {
                        item["id"]: item for item in parsed_info[el]
                        if str(item["id"]) not in str(items_id_list)
                    }
                    item_prices_all = [item["price"] for item in parsed_info[el]]
                    item_prices_opponent = [item["price"] for item in filtered_dict.values()]
                    max_site_price = self.get_site_price(
                        self.steam_inventory_phases[items_list[item]["assetid"]], seller_value, 'max')

                    min_site_price = self.get_site_price(
                        self.steam_inventory_phases[items_list[item]["assetid"]], seller_value, 'min')

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
                        if item_['item_id'] == item_id and item_['price'] != my_price / 100:
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
            item_name = item['market_hash_name']
            if item_name not in seen:
                unique_items.append(item)
                seen.add(item_name)
        for hash_name in unique_items:
            coded_item_name = urllib.parse.quote(hash_name['market_hash_name'])
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
            list_hash_names = '&list_hash_name[]=' + '&list_hash_name[]='.join(hash_names)
            search_hash_name_url = (f'{self.site_url}/api/v2/search-list-items-by-hash-name-all?'
                                    f'key={api_key}{list_hash_names}')
            parsed_info = requests.get(search_hash_name_url, timeout=15).json()
            if parsed_info['success'] and parsed_info['currency'] == 'RUB' and len(parsed_info['data']) > 0:
                info_to_write = parsed_info['data']
                with results_lock:
                    results.update(info_to_write)
        except:
            pass
        time.sleep(1)
        del threads[api_key]

    # endregion

    # endregion
