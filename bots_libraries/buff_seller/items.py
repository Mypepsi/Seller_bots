import math
import time
import requests
import threading
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
                    max_items_count = 20
                    filtered_inventory = [inventory[i:i + max_items_count] for i in range(0, len(inventory), max_items_count)]
                    seller_value = self.get_information_for_price()
                    if filtered_inventory and seller_value:
                        for items_list in filtered_inventory:
                            data = {
                                "assets": [],
                                "game": "csgo"
                            }

                            headers = {
                                "Host": "buff.163.com",
                                "Origin": "https://buff.163.com",
                                "Referer": "https://buff.163.com/market/steam_inventory?game=csgo",
                                "X-CSRFToken": self.buff_cookie.get("csrf_token")
                            }
                            for item in items_list:
                                asset_id = str(item['asset_info']['assetid'])
                                site_price = self.get_site_price(self.steam_inventory_phases[asset_id],
                                                                 seller_value, 'max')
                                if site_price is not None and site_price != 0:
                                    item_name = self.steam_inventory_phases[str(asset_id)]["market_hash_name"]
                                    item_price_income = math.floor(site_price * 0.975 * 100) / 100,
                                    item_data = {
                                        "game": "csgo",
                                        "market_hash_name": item_name,
                                        "contextid": 2,
                                        "assetid": asset_id,
                                        "classid": item["classid"],
                                        "instanceid": item["instanceid"],
                                        "goods_id": item["goods_id"],
                                        "price": site_price,
                                        "income": item_price_income,
                                        "has_market_min_price": False,
                                        "reward_points": math.ceil(site_price),
                                        "cdkey_id": "",
                                    }

                                    data["assets"].append(item_data)
                            try:
                                list_items_steam_url = f'{self.site_url}/api/market/sell_order/create/manual_plus'
                                requests.post(list_items_steam_url, headers=headers, cookies=self.buff_cookie,
                                              json=data, timeout=15)
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
            page_num = 1
            my_inventory = []
            while True:
                try:
                    my_inventory_url = (f'{self.site_url}/api/market/steam_inventory?game=csgo&force=0'
                                        f'&page_num={page_num}&page_size=500&search=&state=tradable'
                                        f'&sort_by=price.desc&_={int(time.time() * 1000)}')
                    my_inventory_response = requests.get(my_inventory_url, cookies=self.buff_cookie, timeout=15).json()
                    if isinstance(my_inventory_response, dict) and my_inventory_response["code"] == 'OK':
                        if my_inventory_response["data"]["total_page"] < page_num:
                            break
                        for item in my_inventory_response["data"]["items"]:
                            if (item["state_toast"] is None and item["progress_text"] == 'Idle'
                                    and item["state_text"] == 'Tradable'):
                                my_inventory.append(item)
                        page_num += 1
                    else:
                        break
                except:
                    break
            acc_data_inventory_assets_id = [int(item['asset_id']) for item in self.steam_inventory_tradable.values()]
            filtered_inventory = [item for item in my_inventory
                                  if int(item['asset_info']['assetid']) in acc_data_inventory_assets_id]
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
                                max_price_with_margin = (max_price *
                                                         condition['days from'][phases_key]['prices'][price_range])
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
                    page_num = 1
                    listed_items = []
                    while True:
                        try:
                            my_inventory_url = (
                                f'{self.site_url}/api/market/steam_inventory?game=csgo&force=0&page_num={page_num}'
                                f'&page_size=500&search=&state=tradable&sort_by=price.desc&_={int(time.time() * 1000)}')
                            my_inventory_response = requests.get(my_inventory_url, cookies=self.buff_cookie,
                                                                 timeout=15).json()

                            if (isinstance(my_inventory_response, dict) and "code" in my_inventory_response
                                    and my_inventory_response["code"] == 'OK'):
                                if my_inventory_response["data"]["total_page"] < page_num:
                                    break
                                listed_items += my_inventory_response["data"]["items"]
                                page_num += 1
                            else:
                                break
                        except:
                            break
                    if listed_items and isinstance(listed_items, list) and len(listed_items) > 0:
                        items_with_status_one = []
                        for item in listed_items:
                            if (item["state_toast"] == 'This item is on sale' and item["progress_text"] == 'On sale'
                                    and item["state_text"] == 'Tradable'):
                                items_with_status_one.append(item)
                        if items_with_status_one:
                            filtered_items = self.change_price_delete_items(items_with_status_one)
                            seller_value = self.get_information_for_price()
                            try:
                                proxy_list = self.search_in_merges_by_username(self.steamclient.username)['proxy']
                            except:
                                proxy_list = None
                            if proxy_list and seller_value and filtered_items:
                                items_count = self.change_price_items_count
                                for i in range(0, len(filtered_items), items_count):
                                    items_list = filtered_items[i:i + items_count]
                                    parsed_info = self.threads_parsing_prices(items_list, proxy_list)
                                    self.change_price_below_opponent(items_list, parsed_info, seller_value, listed_items)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Change Price Global Error: {e}", self.steamclient.username)
            time.sleep(self.change_price_global_time)

    def change_price_delete_items(self, items_on_sale):
        items_id_to_delete = []
        tradable_asset_id = list(self.steam_inventory_tradable.keys())
        for item in items_on_sale:
            if item['asset_info']['assetid'] not in tradable_asset_id:
                items_id_to_delete.append(item["sell_order_id"])
        if len(items_id_to_delete) > 0:
            self.process_items(items_id_to_delete)
        filtered_items = []
        for item in items_on_sale:
            if 'item_id' in item and item["item_id"] not in items_id_to_delete:
                filtered_items.append(item)
        return filtered_items
    #
    # def request_to_delete_items(self, items_to_delete):
    #     items_count_in_request = self.change_price_items_count_in_request
    #     for i in range(0, len(items_to_delete), items_count_in_request):
    #         json_data = {
    #             "game": "csgo",
    #             "sell_orders": items_to_delete[i:i + items_count_in_request]
    #         }
    #
    #         headers = {
    #             "Host": "buff.163.com",
    #             "Origin": "https://buff.163.com",
    #             "Referer": "https://buff.163.com/market/sell_order/on_sale?game=csgo&mode=2,5",
    #             "X-CSRFToken": self.buff_cookie.get("csrf_token")
    #         }
    #         try:
    #             delete_url = f'{self.site_url}/api/market/sell_order/cancel'
    #             requests.post(delete_url, headers=headers, data=json_data, timeout=15)
    #         except:
    #             pass
    #         time.sleep(2)

    def change_price_below_opponent(self, items_list, parsed_info, seller_value, listed_items):
        print(f'items_list= {items_list}')
        print(f'parsed_info= {parsed_info}')
        print(f'seller_value= {seller_value}')
        print(f'listed_items= {listed_items}')
        my_prices = []
        items_id_list = [item['asset_info']['assetid'] for item in items_list]
        for item in range(len(items_list)):
            market_hash_name = items_list[item]['market_hash_name']
            assetid = items_list[item]['asset_info']['assetid']
            for el in parsed_info.keys():
                print(el)
                print(assetid)
                if el == market_hash_name:
                    filtered_dict = {
                        item['asset_info']['assetid']: item for item in parsed_info[el]
                        if str(item['asset_info']['assetid']) not in str(items_id_list)
                    }
                    item_prices_all = [item["price"] for item in parsed_info[el]]
                    item_prices_opponent = [item["price"] for item in filtered_dict.values()]
                    max_site_price = self.get_site_price(
                        self.steam_inventory_phases[items_list[item]['asset_info']['assetid']], seller_value, 'max')

                    min_site_price = self.get_site_price(
                        self.steam_inventory_phases[items_list[item]['asset_info']['assetid']], seller_value, 'min')
                    print(len(item_prices_opponent))
                    print(min_site_price)
                    print(max_site_price)
                    if len(item_prices_opponent) > 0 and min_site_price is not None and max_site_price is not None:
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
                                                  f"{self.steam_inventory_phases[items_list[item]['assetid']]} assetID",
                                    self.steamclient.username)
                        break
                    for item_ in listed_items:
                        if item_['asset_info']['assetid'] == assetid and item_['sell_order_price'] != my_price:
                            data = {
                                "cdkey_id": "",
                                "desc": "",
                                "goods_id": item_["goods_id"],
                                "has_market_min_price": False,
                                "income": math.floor(my_price * 0.975 * 100) / 100,
                                "origin_price": item_["sell_order_price"],
                                "paintwear": item_['asset_info']["paintwear"],
                                "price": my_price,
                                "reward_points": 0,
                                "sell_order_id": item_['sell_order_id']
                            }
                            print(item_)
                            my_prices.append(data)
                            break
                    break
        if len(my_prices) > 0:
            print(my_prices)
            self.process_items(my_prices, only_remove=False)

    def process_items(self, items, only_remove=True):
        items_count_in_request = self.change_price_items_count_in_request

        if only_remove:
            url = f'{self.site_url}/api/market/sell_order/cancel'
        else:
            url = f'{self.site_url}/api/market/sell_order/change'

        for i in range(0, len(items), items_count_in_request):
            data = {
                "game": "csgo",
                "sell_orders": items[i:i + items_count_in_request]
            }
            print(data)
            headers = {
                "Host": "buff.163.com",
                "Origin": "https://buff.163.com",
                "Referer": "https://buff.163.com/market/sell_order/on_sale?game=csgo&mode=2,5",
                "X-CSRFToken": self.buff_cookie.get("csrf_token")
            }
            try:
                r = requests.post(url, cookies=self.buff_cookie, headers=headers, json=data, timeout=15)
                print(r.json())
            except:
                pass

            time.sleep(2)

    # region Parsing Info for change price
    def threads_parsing_prices(self, items, proxy_list):
        threads = {}
        results = {}
        results_lock = threading.Lock()
        hash_queue = Queue()
        unique_items = []
        seen = set()
        for item in items:
            goods_id = item['goods_id']
            if goods_id not in seen:
                unique_items.append(item)
                seen.add(goods_id)
        for item in unique_items:
            hash_queue.put(item['goods_id'])
        while not hash_queue.empty():
            for proxy in proxy_list:
                if proxy not in threads and not hash_queue.empty():
                    goods_ids = []
                    items_for_parse = 1
                    for _ in range(min(items_for_parse, hash_queue.qsize())):
                        try:
                            goods_ids.append(hash_queue.get_nowait())
                        except Empty:
                            break
                    thread = threading.Thread(target=self.request_to_parsing_prices,
                                              args=(proxy, goods_ids[0], results, results_lock, threads))
                    thread.start()
                    threads[proxy] = thread
            time.sleep(1)
        while True:
            if len(threads) == 0:
                break
            time.sleep(1)
        return results

    def request_to_parsing_prices(self, api_key, goods_id, results, results_lock, threads):
        try:
            search_hash_name_url = (f'{self.site_url}/api/market/goods/sell_order?game=csgo&goods_id={goods_id}'
                                    f'&page_num=1&sort_by=default&mode=&allow_tradable_cooldown=1&{int(time.time() * 1000)}')
            parsed_info = requests.get(search_hash_name_url, timeout=15).json()
            if parsed_info['code'] and parsed_info['code'] == 'OK' and len(parsed_info['data']['items']) > 0:
                market_hash_name = next(iter(parsed_info['data']['goods_infos'].values()))['market_hash_name']
                info_to_write = {market_hash_name: parsed_info['data']['items']}
                with results_lock:
                    results.update(info_to_write)
        except:
            pass
        time.sleep(2)
        del threads[api_key]

    # endregion

    # endregion
