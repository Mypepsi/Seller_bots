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
            if keys[i] <= wanted < keys[i + 1]:
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
                phases_difference = (current_timestamp - start_sale_time) // 86400
                phases_key = self.find_matching_key(phases_difference, condition['days from'])
                all_prices = self.content_database_prices['DataBasePrices']
                for price in all_prices:
                    if hash_name in price:
                        max_price = float(price[hash_name]["max_price"])
                        price_range = self.find_matching_key(max_price,
                                                             condition['days from'][phases_key]['prices'])
                        margin_max_price = max_price * condition['days from'][phases_key]['prices'][price_range]
                        limits_margin_max_price = (margin_max_price *
                                                   condition['days from'][phases_key]['limits'][limits_value])

                        try:
                            my_market_price = round(limits_margin_max_price * self.commission * self.rate, 2)
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
            time.sleep(3)
            my_inventory_url = f'https://market.csgo.com/api/v2/my-inventory/?key={self.steamclient.tm_api}'
            try:
                my_inventory = requests.get(my_inventory_url, timeout=30).json()
            except:
                my_inventory = {}
            my_inventory_list = []
            if 'success' in my_inventory and my_inventory['success']:
                try:
                    my_inventory_items = my_inventory['items']
                    my_inventory_list = [item['id'] for item in my_inventory_items]
                except Exception:
                    pass
            else:
                Logs.log('Error during receiving inventory')

            acc_data_inventory_assets_id = [item['asset_id'] for item in inventory_from_acc_data.values()]
            filtered_inventory = [item for item in my_inventory_list if item in acc_data_inventory_assets_id]
            return filtered_inventory
        except:
            return None

    def add_to_sale(self, acc_info, time_sleep):
        while True:
            self.update_account_data_info()
            self.update_db_prices_and_setting()
            acc_data_tradable_inventory = {}
            acc_data_phases_inventory = {}
            username = ''
            try:
                acc_data_tradable_inventory = acc_info['steam inventory tradable']
                acc_data_phases_inventory = acc_info['steam inventory phases']
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
            except:
                Logs.log('Error during taking a session')
            filtered_inventory = self.get_and_filtered_inventory(acc_data_tradable_inventory)
            tm_seller_value = self.taking_tm_information_for_pricing()

            for asset_id in filtered_inventory:
                try:
                    market_price = self.get_my_market_price(acc_data_phases_inventory[asset_id], tm_seller_value, 'max')
                    add_to_sale_url = (f'https://market.csgo.com/api/v2/add-to-sale?key={self.steamclient.tm_api}'
                           f'&cur=RUB&id={asset_id}&price={market_price}')
                    requests.get(add_to_sale_url, timeout=20)
                except:
                    Logs.log(f'{username}:{asset_id} not put up for sale')
                time.sleep(2)

            time.sleep(time_sleep)
    #endregion

    # region change price
    def get_store_items(self):
        try:
            exhibited_items_url = f'https://market.csgo.com/api/v2/items?key={self.steamclient.tm_api}'
            response = requests.get(exhibited_items_url, timeout=20).json()
            return response
        except Exception:
            Logs.log(f'{self.steamclient.username}: Change Price request error')
            return None

    def delete_item_from_sale(self, tradable_inventory, items_on_sale):
        asset_id_to_delete = []
        try:
            asset_id_on_sale = [item["assetid"] for item in items_on_sale]
            tradable_asset_id = list(tradable_inventory.keys())
            for assetid in asset_id_on_sale:
                if assetid not in tradable_asset_id:
                    asset_id_to_delete.append(assetid)
        except:
            Logs.log(f'{self.steamclient.username}: Error in delete_item_from_sale')

        ...  # DELETE FROM SALE REQUEST
        filtered_items = []
        for item in items_on_sale:
            if item["assetid"] not in asset_id_to_delete:
                filtered_items.append(item)
        return filtered_items

    # region parsing info
    def parsing_prices(self, api_key, hash_names, results, results_lock):
        try:
            list_hash_names = '&list_hash_name[]=' + '&list_hash_name[]='.join(hash_names)
            search_hash_name_url = (f'https://market.csgo.com/api/v2/search-list-items-by-hash-name-all?'
                                    f'key={api_key}&extended=1{list_hash_names}')
            parsed_info = requests.get(search_hash_name_url, timeout=20).json()
            with results_lock:
                results.append(parsed_info)
        except:
            pass

    def threads_to_parsing(self, items, api_keys):
        threads = []
        results = []
        try:
            results_lock = threading.Lock()
            hash_queue = Queue()

            items = list(set(items))

            for hash_name in items:
                coded_item_name = urllib.parse.quote(hash_name)
                hash_queue.put(coded_item_name)

            while not hash_queue.empty():
                hash_names = []
                for _ in range(min(50, hash_queue.qsize())):
                    try:
                        hash_names.append(hash_queue.get_nowait())
                    except Empty:
                        break

                for api_key in api_keys:
                    time.sleep(1)
                    thread = threading.Thread(target=self.parsing_prices,
                                              args=(api_key, hash_names, results, results_lock))
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join()

                threads = []

            return results

        except:
            return results
    # endregion

    def change_price(self, acc_info, time_sleep):
        while True:
            username = ''
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
            if 'items' in store_items and type(store_items['items']) == list:
                new_store_items = self.delete_item_from_sale(acc_data_tradable_inventory, store_items['items'])
                try:
                    another_tm_apis_list = self.search_in_merges_by_username(self.steamclient.username)['tm apikey']
                    items_asset_ids = [item["item_id"] for item in new_store_items]
                    parsed_info = self.threads_to_parsing(new_store_items, another_tm_apis_list)
                    my_prices = {}
                    for i in range(len(new_store_items)):
                        try:
                            item_status = new_store_items[i]['status']
                            if item_status != '1':
                                continue
                            item_name = new_store_items[i]['market_hash_name']
                            for el in parsed_info:
                                if ('data' in el and isinstance(el['data'], list)
                                        and 'currency' in el and el['currency'] == 'RUB'):
                                    filtered_dict = {
                                        key: value for key, value in el['data'].items()
                                        if value["id"] not in items_asset_ids
                                    }
                                    if filtered_dict:
                                        item_prices = [item["price"] for item in filtered_dict[item_name]]
                                        tm_seller_value = self.taking_tm_information_for_pricing()

                                        max_market_price = self.get_my_market_price(
                                            acc_data_phases_inventory[new_store_items[i]["assetid"]], tm_seller_value, 'max')

                                        min_market_price = self.get_my_market_price(
                                            acc_data_phases_inventory[new_store_items[i]["assetid"]], tm_seller_value, 'min')

                                        if len(item_prices) > 0:
                                            min_price_raw = min([int(price) for price in item_prices])
                                            min_price = (min_price_raw - 1) / 100

                                            if min_market_price <= min_price <= max_market_price:
                                                my_market_price = min_price
                                            elif min_price - 1 < min_market_price:
                                                my_market_price = min_market_price
                                            else:
                                                my_market_price = max_market_price
                                        else:
                                            my_market_price = max_market_price

                                        coded_item_name = urllib.parse.quote(item_name)
                                        my_prices[coded_item_name] = my_market_price

                        except Exception as e:
                            Logs.log(f'{username}: Error in change_price: {e}')

                    for key, value in my_prices:
                        change_price_url = f'{value}/{key}'
                        try:
                            requests.get(change_price_url, timeout=30)
                        except:
                            pass

                except Exception as e:
                    Logs.log(f'{username}: Fatal error in change_price: {e}')

            time.sleep(time_sleep)

    #endregion

