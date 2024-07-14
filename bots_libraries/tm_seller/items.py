from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.thread_manager import ThreadManager
from queue import Queue, Empty
import urllib.parse
import threading
import time
import requests
import urllib.parse


class TMItems(ThreadManager):
    def __init__(self):
        super().__init__()


    # region functions for add to sale and change price

    def taking_tm_information_for_pricing(self):
        try:
            self.commission = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_commission']
            self.rate = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_rate']
        except:
            Logs.log(f'Error during taking a info from DataBaseSettings -> TM_Seller')
        try:
            database_setting_bots = self.content_database_settings['DataBaseSettings']['Sellers_SalePrice']['bots']
        except:
            database_setting_bots = {}
            Logs.log(f'Error during taking a info from DataBaseSettings -> Sellers_SalePrice -> bots')

        tm_seller_value = None
        for key, value in database_setting_bots.items():
            if 'tm_seller' in key:
                tm_seller_value = value
                break
        return tm_seller_value

    @staticmethod
    def find_matching_key(wanted, dictionary):
        keys = sorted([float(k) for k in dictionary.keys()])
        found_key = None
        for i in range(len(keys) - 1):
            if wanted >= keys[i]:
                found_key = str(int(keys[i])) if keys[i].is_integer() else str(keys[i])
            elif keys[i] <= wanted < keys[i + 1]:
                if keys[i].is_integer():
                    found_key = str(int(keys[i]))
                else:
                    found_key = str(keys[i])
                break
        if found_key is None and wanted >= keys[-1]:
            found_key = str(keys[-1])
        return found_key

    def get_my_market_price(self, asset_id_in_phases_inventory, conditions, limits_value):
        start_sale_time = asset_id_in_phases_inventory['time']
        hash_name = asset_id_in_phases_inventory['market_hash_name']
        for condition in conditions:
            if condition['date to'] >= start_sale_time >= condition['date from']:
                current_timestamp = int(time.time())
                phases_difference = (current_timestamp - start_sale_time) / 86400
                phases_key = str(self.find_matching_key(phases_difference, condition['days from']))
                all_prices = self.content_database_prices['DataBasePrices']
                for price in all_prices:
                    if hash_name in price:
                        try:
                            max_price = float(price[hash_name]["max_price"])
                            price_range = self.find_matching_key(max_price,
                                                                 condition['days from'][phases_key]['prices'])
                            margin_max_price = max_price * condition['days from'][phases_key]['prices'][price_range]
                            limits_margin_max_price = (margin_max_price *
                                                       condition['days from'][phases_key]['limits'][limits_value])

                            my_market_price = round(limits_margin_max_price * 100 * self.rate / self.commission)
                        except:
                            my_market_price = 0
                        return my_market_price
        return None
    # endregion

    #region add to sale
    def get_and_filtered_inventory(self, inventory_from_acc_data):
        try:
            update_inventory_url = f'https://market.csgo.com/api/v2/update-inventory/?key={self.steamclient.tm_api}'
            try:
                requests.get(update_inventory_url, timeout=30)
            except:
                pass
            time.sleep(5)
            my_inventory_url = f'https://market.csgo.com/api/v2/my-inventory/?key={self.steamclient.tm_api}'
            try:
                my_inventory = requests.get(my_inventory_url, timeout=30).json()
            except:
                my_inventory = None
            my_inventory_list = []
            if my_inventory is not None and 'success' in my_inventory and my_inventory['success']:
                try:
                    my_inventory_items = my_inventory['items']
                    my_inventory_list = [item['id'] for item in my_inventory_items]
                except Exception:
                    pass
            elif my_inventory is not None:
                Logs.log('Error during receiving inventory')

            acc_data_inventory_assets_id = [item['asset_id'] for item in inventory_from_acc_data.values()]
            filtered_inventory = [item for item in my_inventory_list if item in acc_data_inventory_assets_id]
            return filtered_inventory
        except:
            return []

    def add_to_sale(self, acc_info, time_sleep):
        while True:
            self.update_account_data_info()
            self.update_db_prices_and_setting()
            acc_data_tradable_inventory = {}
            acc_data_phases_inventory = {}
            try:
                acc_data_tradable_inventory = acc_info['steam inventory tradable']
                acc_data_phases_inventory = acc_info['steam inventory phases']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
            except:
                Logs.log('Error during taking a session')
            filtered_inventory = self.get_and_filtered_inventory(acc_data_tradable_inventory)
            tm_seller_value = self.taking_tm_information_for_pricing()

            for asset_id in filtered_inventory:
                try:
                    market_price = self.get_my_market_price(acc_data_phases_inventory[asset_id], tm_seller_value, 'max')
                    if market_price is not None and market_price != 0:
                        add_to_sale_url = (f'https://market.csgo.com/api/v2/add-to-sale?key={self.steamclient.tm_api}'
                                           f'&cur=RUB&id={asset_id}&price={market_price}')
                        requests.get(add_to_sale_url, timeout=30)
                except:
                    pass
                time.sleep(2)

            time.sleep(time_sleep)
    #endregion

    # region change price
    def get_store_items(self):
        try:
            exhibited_items_url = f'https://market.csgo.com/api/v2/items?key={self.steamclient.tm_api}'
            response = requests.get(exhibited_items_url, timeout=30).json()
            return response
        except:
            return None

    def delete_item_from_sale(self, tradable_inventory, items_on_sale):
        asset_id_to_delete = []
        item_id_to_delete = {}
        try:
            asset_id_on_sale = [item["assetid"] for item in items_on_sale]
            tradable_asset_id = list(tradable_inventory.keys())
            for assetid in asset_id_on_sale:
                if assetid not in tradable_asset_id:
                    asset_id_to_delete.append(assetid)
                    for item in items_on_sale:
                        if assetid == item["assetid"]:
                            item_id_to_delete[item["item_id"]] = 0
        except:
            Logs.log(f'{self.steamclient.username}: Error in delete_item_from_sale')
        self.request_mass_change_price(item_id_to_delete)
        filtered_items = []
        for item in items_on_sale:
            if 'assetid' in item and item["assetid"] not in asset_id_to_delete:
                filtered_items.append(item)
        return filtered_items

    def request_mass_change_price(self, item_id_to_delete):
        url_to_delete = 'https://market.csgo.com/api/MassSetPriceById/'
        item_to_remove = 100
        for i in range(0, len(item_id_to_delete), item_to_remove):
            sublist_keys = list(item_id_to_delete.keys())[i:i + item_to_remove]
            sublist = {k: item_id_to_delete[k] for k in sublist_keys}
            items = {ui_id: item_id_to_delete[ui_id] for ui_id in sublist}
            params = {'key': self.steamclient.tm_api}
            data = {f'list[{ui_id}]': price for ui_id, price in items.items()}
            try:
                r = requests.post(url_to_delete, params=params, data=data, timeout=30).json()
                print(f"otvet ot change price {len(r['items'])} {r}")
            except:
                pass
            time.sleep(60)

    # region parsing info
    def parsing_prices(self, api_key, hash_names, results, results_lock, threads):
        try:
            list_hash_names = '&list_hash_name[]=' + '&list_hash_name[]='.join(hash_names)
            search_hash_name_url = (f'https://market.csgo.com/api/v2/search-list-items-by-hash-name-all?'
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

    def threads_to_parsing(self, items, api_keys):
        threads = {}
        results = {}
        try:
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
                        thread = threading.Thread(target=self.parsing_prices,
                                                  args=(api_key, hash_names, results, results_lock, threads))
                        thread.start()
                        threads[api_key] = thread
                time.sleep(0.5)
            while True:
                if len(threads) == 0:
                    break
                time.sleep(1)
            return results
        except:
            return results
    # endregion

    def change_price(self, acc_info, time_sleep):
        username = ''
        while True:
            self.update_account_data_info()
            self.update_db_prices_and_setting()
            acc_data_tradable_inventory = {}
            acc_data_phases_inventory = {}
            try:
                acc_data_tradable_inventory = acc_info['steam inventory tradable']
                acc_data_phases_inventory = acc_info['steam inventory phases']
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
            except:
                Logs.log('Error during taking a session')

            store_items = self.get_store_items()
            if store_items is not None and 'items' in store_items and type(store_items['items']) == list:
                item_to_delete = []
                for item in store_items['items']:
                    item_status = item['status']
                    if item_status == '1':
                        item_to_delete.append(item)
                new_store_items = self.delete_item_from_sale(acc_data_tradable_inventory, item_to_delete)
                max_items_count = 100
                for i in range(0, len(new_store_items), max_items_count):
                    sublist = new_store_items[i:i + max_items_count]
                    try:
                        another_tm_apis_list = self.search_in_merges_by_username(self.steamclient.username)['tm apikey']
                        items_item_ids = [item["item_id"] for item in sublist]
                        parsed_info = self.threads_to_parsing(sublist, another_tm_apis_list)
                        my_prices = {}
                        for item in range(len(sublist)):
                            try:
                                item_name = sublist[item]['market_hash_name']
                                item_id = sublist[item]['item_id']
                                for el in parsed_info.keys():
                                    if el == item_name:
                                        filtered_dict = {
                                            item["id"]: item for item in parsed_info[el]
                                            if str(item["id"]) not in str(items_item_ids)
                                        }
                                        if filtered_dict:
                                            item_prices_with_my = [item["price"] for item in parsed_info[el]]
                                            item_prices = [item["price"] for item in filtered_dict.values()]
                                            tm_seller_value = self.taking_tm_information_for_pricing()

                                            max_market_price = self.get_my_market_price(
                                                acc_data_phases_inventory[sublist[item]["assetid"]], tm_seller_value, 'max')

                                            min_market_price = self.get_my_market_price(
                                                acc_data_phases_inventory[sublist[item]["assetid"]], tm_seller_value, 'min')

                                            if len(item_prices) > 0:
                                                min_price_raw = min([int(price) for price in item_prices])
                                                min_price_opponent = (min_price_raw - 1)

                                                if min_market_price <= min_price_opponent <= max_market_price:
                                                    my_market_price = min_price_opponent
                                                elif min_price_opponent < min_market_price:
                                                    my_market_price = min_market_price
                                                else:
                                                    my_market_price = max_market_price
                                            elif len(item_prices) == 0 and len(item_prices_with_my) > 0:
                                                my_market_price = max_market_price
                                            else:
                                                continue
                                            for item_ in store_items['items']:
                                                if (item_['item_id'] == item_id and my_market_price != 0 and
                                                        item_['price'] != my_market_price / 100):
                                                    my_prices[sublist[item]["item_id"]] = my_market_price

                            except Exception as e:
                                Logs.log(f'{username}: Error in change_price: {e}')

                        if len(my_prices) > 0:
                            self.request_mass_change_price(my_prices)

                    except Exception as e:
                        Logs.log(f'{username}: Fatal error in change_price: {e}')
            elif store_items is not None:
                Logs.log('Error during receiving inventory')

            time.sleep(time_sleep)

    #endregion

