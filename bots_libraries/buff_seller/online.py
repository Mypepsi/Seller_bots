import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.sellpy.logs import Logs, ExitException


class BuffOnline(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.ping_alert = False
        self.inventory_errors = self.listed_errors = self.store_errors = 0

    def ping(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    response = self.request_to_ping(0)
                    if response and "error" in response:
                        Logs.log(f"Ping: Error to ping: {response['error']}", self.steamclient.username)
                        if not self.ping_alert:
                            Logs.notify(self.tg_info, f"Ping: Error to ping: {response['error']}",
                                        self.steamclient.username)
                            self.ping_alert = True
            except Exception as e:
                Logs.notify_except(self.tg_info, f'Ping Global Error: {e}', self.steamclient.username)
            time.sleep(self.ping_global_time)

    def request_to_ping(self, status, timeout=15):
        try:
            url_to_ping = f'{self.site_url}/api/market/user_store/change_state'
            headers = {
                "Host": "buff.163.com",
                "Origin": "https://buff.163.com",
                "Referer": "https://buff.163.com/market/sell_order/on_sale?game=csgo&mode=2,5",
                "X-CSRFToken": self.buff_cookie.get("csrf_token"),
                'User-Agent': self.steamclient.user_agent
            }
            json_data = {
                "state": f"{status}",
                "auto_offline": "0",
                "auto_offline_hour": "",
                "auto_offline_minute": ""
            }
            response = requests.post(url_to_ping, json=json_data, headers=headers, cookies=self.buff_cookie,
                                     timeout=timeout).json()
            return response
        except:
            return None

    def restart_store(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    self.request_to_ping(1)
                    time.sleep(1)
                    self.request_to_ping(0)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Restart Store Global Error: {e}", self.steamclient.username)
            time.sleep(self.restart_store_global_time)

    # region Visible Store
    def visible_store(self):  # Global Function (class_for_account_functions)
        while True:
            time.sleep(self.visible_store_global_time)
            try:
                if self.active_session:
                    self.visible_store_inventory()
                    self.visible_store_listed()
                    self.visible_store_online()
            except ExitException:
                break
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Visible Store Global Error: {e}", self.steamclient.username)

    def visible_store_inventory(self):
        page_num = 1
        my_inventory = []
        while True:
            try:
                my_inventory_url = (f'{self.site_url}/api/market/steam_inventory?game=csgo&force=0&page_num={page_num}'
                                    f'&page_size=500&search=&state=tradable&sort_by=price.desc&_={int(time.time() * 1000)}')
                my_inventory_response = requests.get(my_inventory_url, cookies=self.buff_cookie, timeout=15).json()

                if (isinstance(my_inventory_response, dict) and "code" in my_inventory_response
                        and my_inventory_response["code"] == 'OK'):
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
        tradable_inventory = []
        for item in my_inventory:
            if 'tradable' in item and item['tradable'] == 1:
                tradable_inventory.append(item)

        if len(tradable_inventory) > self.visible_store_max_number_of_inv_items:
            self.inventory_errors += 1
        else:
            self.inventory_errors = 0

        if self.inventory_errors > self.visible_store_max_number_of_errors:
            Logs.notify(self.tg_info, f"Visible Store: {len(tradable_inventory)} items not listed on sale",
                        self.steamclient.username)
            raise ExitException
        time.sleep(1)

    def visible_store_listed(self):
        try:
            items_url = (f'{self.site_url}/api/market/steam_inventory?game=csgo&force=0&page_num=1&page_size=500&'
                         f'search=&state=tradable&sort_by=price.desc&_={int(time.time() * 1000)}')
            response = requests.get(items_url, cookies=self.buff_cookie, timeout=15).json()
            items_on_sale = response["data"]["items"]
        except:
            items_on_sale = None

        if items_on_sale and len(items_on_sale) != 0:
            for _ in range(len(items_on_sale)):
                random_item = random.choice(items_on_sale)
                if random_item["items_on_sale"] == 'On sale' and random_item["state_toast"] == 'This item is on sale':
                    asset_id = random_item['asset_info']['assetid']
                    search_list = []
                    page_num = 1
                    while True:
                        try:
                            search_url = (f'{self.site_url}api/market/shop/{self.buff_user_id}/sell_order?tab=selling'
                                          f'&game=csgo&page_num={page_num}&page_size=500&_={int(time.time() * 1000)}')
                            search_response = requests.get(search_url, cookies=self.buff_cookie, timeout=15).json()
                            if (isinstance(search_response, dict) and "code" in search_response
                                    and search_response["code"] == 'OK'):
                                if search_response["data"]["total_page"] < page_num:
                                    break
                                search_list += search_response["data"]["items"]
                                page_num += 1
                            else:
                                break
                            time.sleep(2)
                        except:
                            break

                    search_result = False
                    if search_list:
                        for dictionary in search_list:
                            if ('asset_info' in dictionary and 'assetid' in dictionary['asset_info']
                                    and str(dictionary['asset_info']['assetid']) == str(asset_id)):
                                search_result = True
                                break

                        if not search_result:
                            self.listed_errors += 1
                        else:
                            self.listed_errors = 0
                    break
        if self.listed_errors > self.visible_store_max_number_of_errors:
            Logs.notify(self.tg_info, 'Visible Store: Items not visible in store', self.steamclient.username)
            raise ExitException
        time.sleep(1)

    def visible_store_online(self):
        try:
            online_url = (f'{self.site_url}/api/market/user_store/info?user_id={self.buff_user_id}'
                          f'&store_state_only=true&_={int(time.time() * 1000)}')
            response = requests.get(online_url, cookies=self.buff_cookie, timeout=15).json()
            online_response = response['data']
        except:
            online_response = None

        if 'store_state' in online_response and online_response['store_state'] == 0:
            self.store_errors = 0
        else:
            self.store_errors += 1
        if self.store_errors > self.visible_store_max_number_of_errors:
            Logs.notify(self.tg_info, 'Visible Store: Offline store, items not visible', self.steamclient.username)
            raise ExitException
    # endregion
