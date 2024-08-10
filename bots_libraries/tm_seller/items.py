import time
import requests
import threading
import urllib.parse
from queue import Queue, Empty
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.thread_manager import ThreadManager


class TMItems(ThreadManager):
    def __init__(self, name):
        super().__init__(name)
    #region Add To Sale
    def add_to_sale(self, acc_info, tg_info, global_time):
        while True:
            try:
                self.update_account_data_info()
                self.update_db_prices_and_settings()
                acc_data_tradable_inventory = acc_info['steam inventory tradable']
                acc_data_phases_inventory = acc_info['steam inventory phases']
                active_session = self.take_session(acc_info, tg_info)
                if active_session:
                    filtered_inventory = self.add_to_sale_inventory(acc_data_tradable_inventory)
                    seller_value = self.get_information_for_price(tg_info, 'tm_seller')
                    if filtered_inventory and seller_value:
                        for asset_id in filtered_inventory:
                            site_price = self.get_site_price(acc_data_phases_inventory[asset_id], seller_value, 'max')
                            if site_price is not None and site_price != 0:
                                try:
                                    add_to_sale_url = (f'{self.tm_url}/api/v2/add-to-sale?key={self.steamclient.tm_api}'
                                                       f'&cur=RUB&id={asset_id}&price={site_price}')
                                    requests.get(add_to_sale_url, timeout=5)
                                except:
                                    pass
                            else:
                                Logs.notify(tg_info, f"Add To Sale: Failed listed item on sale: {asset_id}",
                                            self.steamclient.username)
                            time.sleep(3)
            except Exception as e:
                Logs.notify_except(tg_info, f"Add To Sale Global Error: {e}", self.steamclient.username)

            time.sleep(global_time)

    def add_to_sale_inventory(self, inventory_from_acc_data):
        try:
            update_inventory_url = f'{self.tm_url}/api/v2/update-inventory/?key={self.steamclient.tm_api}'
            requests.get(update_inventory_url, timeout=5)
        except:
            pass
        time.sleep(10)
        try:
            my_inventory_url = f'{self.tm_url}/api/v2/my-inventory/?key={self.steamclient.tm_api}'
            my_inventory = requests.get(my_inventory_url, timeout=30).json()
            my_inventory_items = my_inventory['items']
            my_inventory_list = [item['id'] for item in my_inventory_items]
            acc_data_inventory_assets_id = [item['asset_id'] for item in inventory_from_acc_data.values()]
            filtered_inventory = [item for item in my_inventory_list if item in acc_data_inventory_assets_id]
            return filtered_inventory
        except:
            return None

    #endregion

    def get_site_price(self, asset_id_in_phases_inventory, conditions, limits_value):
        start_sale_time = hash_name = None
        try:
            start_sale_time = asset_id_in_phases_inventory['time']
            hash_name = asset_id_in_phases_inventory['market_hash_name']
            self.commission = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_commission']
            self.rate = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_rate']
        except:
            pass
        if start_sale_time and hash_name and self.commission and self.rate:
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
                                max_price_with_margin = max_price * condition['days from'][phases_key]['prices'][price_range]
                                max_price_with_margin_limits = (max_price_with_margin *
                                                           condition['days from'][phases_key]['limits'][limits_value])

                                site_price = round(max_price_with_margin_limits * 100 * self.rate / self.commission)
                            return site_price
        return None

    # region Change Price
    def change_price(self, acc_info, tg_info, global_time):
        while True:
            try:
                self.update_account_data_info()
                self.update_db_prices_and_settings()
                acc_data_tradable_inventory = acc_info['steam inventory tradable']
                acc_data_phases_inventory = acc_info['steam inventory phases']
                active_session = self.take_session(acc_info, tg_info)
                if active_session:
                    try:
                        exhibited_items_url = f'{self.tm_url}/api/v2/items?key={self.steamclient.tm_api}'
                        listed_items = requests.get(exhibited_items_url, timeout=30).json()
                    except:
                        listed_items = None
                    items_with_status_one = []
                    for item in listed_items['items']:
                        item_status = item['status']
                        if item_status == '1':
                            items_with_status_one.append(item)
                    if not items_with_status_one:
                        new_listed_items = self.change_price_delete_items(acc_data_tradable_inventory, items_with_status_one)
                        seller_value = self.get_information_for_price(tg_info, 'tm_seller')
                        if seller_value:
                            max_items_count = 100
                            try:
                                another_tm_apis_list = self.search_in_merges_by_username(tg_info, self.steamclient.username)['tm apikey']
                            except:
                                another_tm_apis_list = None
                            if another_tm_apis_list:
                                for i in range(0, len(new_listed_items), max_items_count):
                                    sublist = new_listed_items[i:i + max_items_count]
                                    parsed_info = self.threads_parsing_prices(sublist, another_tm_apis_list)
                                    my_prices = {}
                                    items_item_ids = [item["item_id"] for item in sublist]
                                    for item in range(len(sublist)):
                                        item_name = sublist[item]['market_hash_name']
                                        item_id = sublist[item]['item_id']
                                        for el in parsed_info.keys():
                                            if el == item_name:
                                                filtered_dict = {
                                                    item["id"]: item for item in parsed_info[el]
                                                    if str(item["id"]) not in str(items_item_ids)
                                                }
                                                item_prices_all = [item["price"] for item in parsed_info[el]]
                                                item_prices_opponent = [item["price"] for item in filtered_dict.values()]
                                                max_site_price = self.get_site_price(
                                                    acc_data_phases_inventory[sublist[item]["assetid"]], seller_value, 'max')

                                                min_site_price = self.get_site_price(
                                                    acc_data_phases_inventory[sublist[item]["assetid"]], seller_value, 'min')

                                                if len(item_prices_opponent) > 0 and min_site_price and max_site_price:
                                                    lower_market_price_opponent = min([int(price) for price in item_prices_opponent])
                                                    min_price_opponent = (lower_market_price_opponent - 1)

                                                    if min_site_price <= min_price_opponent <= max_site_price:
                                                        my_price = min_price_opponent
                                                    elif min_price_opponent < min_site_price:
                                                        my_price = min_site_price
                                                    else:
                                                        my_price = max_site_price
                                                elif len(item_prices_opponent) == 0 and len(item_prices_all) > 0:
                                                    my_price = max_site_price
                                                else:
                                                    Logs.log(f"Change Price:"
                                                             f" Unable to calculate new price for item on sale:"
                                                             f" {acc_data_phases_inventory[sublist[item]['assetid']]}",
                                                             self.steamclient.username)
                                                    break
                                                for item_ in listed_items['items']:
                                                    if (item_['item_id'] == item_id and my_price != 0 and
                                                            item_['price'] != my_price / 100):
                                                        my_prices[sublist[item]["item_id"]] = my_price


                                        if len(my_prices) > 0:
                                            self.request_change_price(my_prices)

            except Exception as e:
                Logs.notify_except(tg_info, f"Change Price Global Error: {e}", self.steamclient.username)
            time.sleep(global_time)

    def change_price_delete_items(self, tradable_inventory, items_on_sale):
        asset_id_to_delete = []
        item_id_to_delete = {}
        asset_id_on_sale = [item["assetid"] for item in items_on_sale]
        tradable_asset_id = list(tradable_inventory.keys())
        for assetid in asset_id_on_sale:
            if assetid not in tradable_asset_id:
                asset_id_to_delete.append(assetid)
                for item in items_on_sale:
                    if assetid == item["assetid"]:
                        item_id_to_delete[item["item_id"]] = 0
        self.request_change_price(item_id_to_delete)
        filtered_items = []
        for item in items_on_sale:
            if 'assetid' in item and item["assetid"] not in asset_id_to_delete:
                filtered_items.append(item)
        return filtered_items

    def request_change_price(self, item_id_to_change_price):
        items_to_change_price = 100
        for i in range(0, len(item_id_to_change_price), items_to_change_price):
            sublist_keys = list(item_id_to_change_price.keys())[i:i + items_to_change_price]
            sublist = {k: item_id_to_change_price[k] for k in sublist_keys}
            items = {ui_id: item_id_to_change_price[ui_id] for ui_id in sublist}
            params = {'key': self.steamclient.tm_api}
            data = {f'list[{ui_id}]': price for ui_id, price in items.items()}
            try:
                url_change_price = f'{self.tm_url}/api/MassSetPriceById/'
                requests.post(url_change_price, params=params, data=data, timeout=5)
            except:
                pass
            time.sleep(65)
    #endregion


    # region Parsing Info
    def threads_parsing_prices(self, items, api_keys):
        threads = {}
        results = {}
        results_lock = threading.Lock()
        hash_queue = Queue()
        unique_items = []
        seen = set()
        for item in items:
            item_id = item['market_hash_name']
            if item_id not in seen:
                unique_items.append(item)
                seen.add(item_id)
        for hash_name in unique_items:
            coded_item_name = urllib.parse.quote(hash_name['market_hash_name'])
            hash_queue.put(coded_item_name)
        while not hash_queue.empty():
            for api_key in api_keys:
                if api_key not in threads and not hash_queue.empty():
                    hash_names = []
                    item_to_parce = 50
                    for _ in range(min(item_to_parce, hash_queue.qsize())):
                        try:
                            hash_names.append(hash_queue.get_nowait())
                        except Empty:
                            break
                    thread = threading.Thread(target=self.request_parsing_prices,
                                              args=(api_key, hash_names, results, results_lock, threads))
                    thread.start()
                    threads[api_key] = thread
            time.sleep(1)
        while True:
            if len(threads) == 0:
                break
            time.sleep(1)
        return results

    def request_parsing_prices(self, api_key, hash_names, results, results_lock, threads):
        try:
            list_hash_names = '&list_hash_name[]=' + '&list_hash_name[]='.join(hash_names)
            search_hash_name_url = (f'{self.tm_url}/api/v2/search-list-items-by-hash-name-all?'
                                    f'key={api_key}{list_hash_names}')
            parsed_info = requests.get(search_hash_name_url, timeout=30).json()
            if parsed_info['success'] and parsed_info['currency'] == 'RUB':
                info_to_write = parsed_info['data']
                with results_lock:
                    results.update(info_to_write)
        except:
            pass
        time.sleep(1)
        del threads[api_key]

    # endregion


