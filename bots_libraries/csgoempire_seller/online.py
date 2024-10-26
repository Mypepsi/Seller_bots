import time
import pyotp
import random
import requests
import urllib.parse
from lxml import html
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.sellpy.logs import Logs, ExitException


class CSGOEmpireOnline(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.inventory_errors = self.listed_errors = 0

    # region Visible Store
    def visible_store(self):  # Global Function (class_for_account_functions)
        while True:
            time.sleep(self.visible_store_global_time)
            try:
                if self.active_session:
                    self.visible_store_inventory()
                    self.visible_store_listed()
            except ExitException:
                break
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Visible Store Global Error: {e}", self.steamclient.username)

    def visible_store_inventory(self):
        try:
            my_inventory_url = f'{self.site_url}/api/v2/trading/user/inventory?update=false'
            my_inventory_response = requests.get(my_inventory_url, headers=self.csgoempire_headers, timeout=15).json()
            my_inventory = my_inventory_response['data']
        except:
            my_inventory = []

        tradable_inventory = []
        for item in my_inventory:
            if 'tradable' in item and item['tradable'] is True and 'invalid' not in item:
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
            items_url = f'{self.site_url}/api/v2/trading/user/trades'
            response = requests.get(items_url, headers=self.csgoempire_headers, timeout=15).json()
            items_on_sale = []
            for item in response['data']['deposits']:
                if 'status_message' in item and item['status_message'] == 'Processing':
                    items_on_sale.append(item)
        except:
            items_on_sale = None

        if items_on_sale and len(items_on_sale) != 0:
            try:
                another_apis_list = self.search_in_merges_by_username(self.steamclient.username)['csgoempire apikey']
            except:
                another_apis_list = None

            if another_apis_list:
                random_item = random.choice(items_on_sale)
                hash_name = random_item['item']['market_name']
                coded_hash_name = urllib.parse.quote(hash_name)
                item_id = random_item['id']
                another_api = random.choice(another_apis_list)

                params = {
                    "per_page": 250,
                    "page": 1,
                    "price_max_above": 99999,
                    "delivery_time_long_max": 99999,
                    "search": coded_hash_name
                }
                headers = {
                    'Authorization': f'Bearer {another_api}'
                }

                try:
                    search_url = f'{self.site_url}/api/v2/trading/items'
                    search_response = requests.get(search_url, params=params, headers=headers, timeout=15).json()
                    search_list = search_response['data']
                except:
                    search_list = None

                search_result = False
                if search_list:
                    for dictionary in search_list:
                        if ('id' in dictionary and str(dictionary['id']) == str(item_id)
                                and 'depositor_stats' in dictionary
                                and 'user_online_status' in dictionary['depositor_stats']
                                and dictionary['depositor_stats']['user_online_status'] == 1):
                            search_result = True
                            break

                if not search_result:
                    self.listed_errors += 1
                else:
                    self.listed_errors = 0

        if self.listed_errors > self.visible_store_max_number_of_errors:
            Logs.notify(self.tg_info, 'Visible Store: Items not visible in store', self.steamclient.username)
            raise ExitException

    # endregion\

    def emp_cookie(self):  # Global Function (class_for_single_function)
        Logs.log(f"CSGOEmpire Cookie: thread are running", '')
        while True:
            self.update_account_settings_info()
            self.update_account_data_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    if self.take_session(acc_info):
                        username = acc_info['username']
                        headers = {"Authorization": f"Bearer {acc_info['csgoempire apikey']}"}
                        current_timestamp = int(time.time())
                        if username in self.content_acc_data_dict:
                            last_update_time = self.content_acc_data_dict[username].get('time csgoempire cookie', 0)
                            difference_to_update = current_timestamp - int(last_update_time)
                            if difference_to_update > self.csgoempire_cookie_validity_time:
                                login_url = 'https://csgoempire.io/login'
                                csgoempire_login_response = self.steamclient._session.get(login_url)
                                tree = html.fromstring(csgoempire_login_response.text)
                                open_id_params = tree.xpath('//input[@name="openidparams"]')
                                nonce = tree.xpath('//input[@name="nonce"]')
                                data_to_send = {
                                    "action": "steam_openid_login",
                                    "openid.mode": "checkid_setup",
                                    "openidparams": open_id_params[0].get('value'),
                                    "nonce": nonce[0].get('value')
                                }
                                self.steamclient._session.post('https://steamcommunity.com/openid/login',
                                                               data=data_to_send)
                                empire_cookie_dict = {
                                    cookie.name: cookie.value
                                    for cookie in self.steamclient._session.cookies
                                    if 'csgoempire.io' in cookie.domain
                                }
                                try:
                                    metadata_url = f'{self.site_url}/api/v2/metadata/socket'
                                    metadata = requests.get(metadata_url, headers=headers, cookies=empire_cookie_dict,
                                                            timeout=15).json()
                                except:
                                    metadata = None
                                try:
                                    uuid = metadata['user']['session']['device_identifier']
                                except:
                                    try:
                                        uuid = metadata['user']['last_session']['device_identifier']
                                    except:
                                        uuid = None


                                self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                    {"$set": {
                                                                        "time csgoempire cookie": current_timestamp,
                                                                        "csgoempire cookie": empire_cookie_dict,
                                                                        "csgoempire uuid": uuid}})
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"CSGOEmpire Cookie Global Error: {e}", username)
                time.sleep(10)
            time.sleep(self.csgoempire_login_global_time)

    def balance_transfer(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Balance Transfer: thread are running", '')
        while True:
            time.sleep(self.balance_transfer_global_time)
            self.update_account_settings_info()
            self.update_database_info(settings=True)
            try:
                steam_id_to_withdraw = self.content_database_settings['DataBaseSettings']['CSGOEmpire_Seller'][
                    'CSGOEmpire_Seller_transfer_steamid']
            except:
                steam_id_to_withdraw = None
            if steam_id_to_withdraw:
                for acc_info in self.content_acc_settings_list:
                    username = None
                    try:
                        username = acc_info['username']
                        secret_key = acc_info['csgoempire 2FA']
                        csgoempire_cookie = self.content_acc_data_dict[username]['csgoempire cookie']
                        csgoempire_uuid = self.content_acc_data_dict[username]['csgoempire uuid']
                        headers = {"Authorization": f"Bearer {acc_info['csgoempire apikey']}"}
                        try:
                            balance_url = f'{self.site_url}/api/v2/metadata/socket'
                            balance_response = requests.get(balance_url, headers=headers, cookies=csgoempire_cookie,
                                                            timeout=15).json()
                            response_money = float(balance_response['user']['balances'][0]['balance']) * 100
                        except:
                            response_money = None
                        if response_money and response_money > 1:
                            time.sleep(3)

                            totp = pyotp.TOTP(secret_key)
                            code = str(totp.now())
                            token_data = {'code': code,
                                          'remember_device': False,
                                          'sid': None,
                                          'type': "onetime",
                                          'uuid': csgoempire_uuid}
                            token_headers = {
                                "X-Empire-Device-Identifier": csgoempire_uuid,
                                "Referer": "https://csgoempire.io/profile/transactions",
                            }
                            try:
                                token_url = f'{self.site_url}/api/v2/user/security/token'
                                token_response = requests.post(token_url, cookies=csgoempire_cookie, json=token_data,
                                                               headers=token_headers, timeout=15).json()
                                token = token_response['token']
                            except:
                                token = None
                            if token:
                                withdrawing_headers = {
                                    "Referer": "https://csgoempire.io/deposit",
                                    "X-Empire-Device-Identifier": csgoempire_uuid,
                                }
                                withdrawing_data = {'amount': response_money,
                                                    'onetime_token': token,
                                                    'steam_id': str(steam_id_to_withdraw)}
                                try:
                                    withdrawing_url = f'{self.site_url}/api/v2/user/chat/tip'
                                    requests.post(withdrawing_url, cookies=csgoempire_cookie,
                                                  headers=withdrawing_headers, json=withdrawing_data, timeout=15)
                                except:
                                    pass
                    except Exception as e:
                        Logs.notify_except(self.tg_info, f"Balance Transfer Global Error: {e}", username)
                    time.sleep(10)
