import time
import random
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class CSGOEmpireGeneral(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    def update_site_data(self):  # Global Function (class_for_account_functions)
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']
                    csgoempire_apikey = acc_info['csgoempire apikey']
                    trade_url = acc_info['trade url']
                    headers = {
                        'Authorization': f'Bearer {csgoempire_apikey}'
                    }
                    data = {"trade_url": trade_url}
                    try:
                        trade_url = f'{self.site_url}/api/v2/trading/user/settings'
                        response = requests.get(trade_url, headers=headers, data=data, timeout=15).json()
                    except:
                        response = None
                    if not (response and response.get('success') and response.get('escrow_seconds') == 0):
                        Logs.notify(self.tg_info, "Update Site Data: Invalid trade url", username)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Site Apikey Global Error: {e}", username)
                time.sleep(10)
            time.sleep(self.update_site_data_global_time)

    def site_apikey(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']
                    headers = {"Authorization": f"Bearer {acc_info['csgoempire apikey']}"}
                    try:
                        balance_url = f'{self.site_url}/api/v2/metadata/socket'
                        response = requests.get(balance_url, headers=headers, timeout=15).json()
                    except:
                        response = None
                    if response and 'invalid_api_token' in response and response['invalid_api_token']:
                        Logs.notify(self.tg_info, 'Site Apikey: Invalid apikey', username)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Site Apikey Global Error: {e}", username)
                time.sleep(10)
            time.sleep(self.site_apikey_global_time)

    def database_csgoempire(self):  # Global Function (class_for_account_functions)
        Logs.log(f"Database CSGOEmpire: thread are running", '')
        while True:
            try:
                current_timestamp = int(time.time())
                try:
                    csgoempire_doc = self.database_csgoempire_collection.find_one()
                except:
                    csgoempire_doc = None
                if csgoempire_doc:
                    last_update_time = int(csgoempire_doc.get("Time", 0))
                else:
                    last_update_time = 0

                difference_to_update = current_timestamp - last_update_time
                if difference_to_update > self.db_csgoempire_validity_time:
                    try:
                        another_apis_list = self.search_in_merges_by_username(
                            self.steamclient.username)['csgoempire apikey']
                    except:
                        another_apis_list = None
                    if another_apis_list:
                        another_api = random.choice(another_apis_list)
                        page = 1
                        params = {
                            "per_page": 2500,
                            "page": page,
                            "price_max_above": 99999,
                            "delivery_time_long_max": 99999
                        }
                        headers = {
                            'Authorization': f'Bearer {another_api}'
                        }
                        counter = 0
                        data = {}
                        while counter < 1:
                            try:
                                search_url = f'{self.site_url}/api/v2/trading/items'
                                search_response = requests.get(search_url, params=params, headers=headers,
                                                               timeout=15).json()
                                for item in search_response['data']:
                                    entry = {'site_item_id': item['id'], 'price': item['market_value']}
                                    if item['market_name'] in data:
                                        data[item['market_name']].append(entry)
                                    else:
                                        data[item['market_name']] = [entry]
                                if search_response.get('success') and len(search_response['data']['listings']) < 2000:
                                    break
                                page += 1
                            except:
                                counter += 1
                            time.sleep(5)
                        csgoempire_dict = {"Time": current_timestamp,
                                           "DataBaseCSGOEmpire": data}
                        try:
                            self.database_csgoempire_collection.replace_one({}, csgoempire_dict, upsert=True)
                            Logs.log(f"Database CSGOEmpire: DB Settings has been updated in MongoDB", '')

                        except Exception as e:
                            Logs.notify_except(self.tg_info,
                                               f"Database CSGOEmpire: MongoDB critical request failed: {e}",
                                               '')
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Database CSGOEmpire Global Error: {e}", '')
            time.sleep(self.db_csgoempire_global_time)
