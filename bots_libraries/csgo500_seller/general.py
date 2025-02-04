import jwt
import time
import random
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.session_manager import SessionManager


class CSGO500General(SessionManager):
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
                    trade_url = acc_info['trade url']
                    steam_apikey = self.content_acc_data_dict[username]['steam apikey']
                    jwt_api_key = jwt.encode(
                        {'userId': acc_info['csgo500 user id']},
                        acc_info['csgo500 apikey'],
                        algorithm="HS256"
                    )
                    csgo500_jwt_apikey = {'x-500-auth': jwt_api_key}
                    try:
                        data = {"tradeUrl": trade_url}
                        tradelink_url = f'{self.site_url}/api/v1/user/set/trade-url'
                        requests.post(tradelink_url, headers=csgo500_jwt_apikey, json=data, timeout=15)
                    except:
                        pass
                    time.sleep(1)
                    if steam_apikey:
                        try:
                            params = {
                                "steamApiKey": steam_apikey
                            }
                            apikey_url = f'{self.site_url}/api/v1/user/set/steam-api-key'
                            requests.post(apikey_url, headers=csgo500_jwt_apikey, data=params, timeout=15)
                        except:
                            pass
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Update Site Data Global Error: {e}", username)
                time.sleep(3)
            time.sleep(self.update_site_data_global_time)

    def site_apikey(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Site Apikey: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc_info in self.content_acc_settings_list:
                username = None
                try:
                    username = acc_info['username']
                    jwt_api_key = jwt.encode(
                        {'userId': acc_info['csgo500 user id']},
                        acc_info['csgo500 apikey'],
                        algorithm="HS256"
                    )
                    try:
                        url = f'{self.site_url}/api/v1/user/balance?type=bux'
                        response = requests.get(url, headers=jwt_api_key, timeout=15).json()
                    except:
                        response = None
                    if response and 'type' in response and response['type'] == 'AuthorizationError':
                        Logs.notify(self.tg_info, 'Site Apikey: Invalid apikey', username)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Site Apikey Global Error: {e}", username)
                time.sleep(10)
            time.sleep(self.site_apikey_global_time)

    def balance_transfer(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Balance Transfer: thread are running", '')
        while True:
            # time.sleep(self.balance_transfer_global_time)
            self.update_account_settings_info()
            self.update_database_info(settings=True)
            try:
                user_id_to_withdraw = self.content_database_settings['DataBaseSettings']['CSGO500_Seller'][
                    'CSGO500_Seller_transfer_user_id']
            except:
                user_id_to_withdraw = None
            user_id_to_withdraw = '5f98b8f552d84a72a18f8138'
            if user_id_to_withdraw:
                for acc_info in self.content_acc_settings_list:
                    username = None
                    try:
                        username = acc_info['username']
                        jwt_api_key = jwt.encode(
                            {'userId': acc_info['csgo500 user id']},
                            acc_info['csgo500 apikey'],
                            algorithm="HS256"
                        )
                        try:
                            current_balance_url = f'{self.site_url}/api/v1/user/balance?type=bux'
                            response = requests.post(current_balance_url, headers={'x-500-auth': jwt_api_key}, timeout=15).json()
                            response_money = response['data']['value']
                        except:
                            response_money = None
                        response_money = 500
                        if response_money and response_money >= 10:
                            time.sleep(1)
                            try:
                                withdrawing_url = f'{self.site_url}/api/v1/user/balance/send'
                                data = {
                                    "balanceType": "bux",
                                    "message": "string",
                                    "destinationUserId": user_id_to_withdraw,
                                    "value": response_money
                                }
                                new_balance = requests.post(withdrawing_url, headers={'x-500-auth': jwt_api_key},
                                                            data=data, timeout=15).json()
                                print(new_balance)
                            except:
                                new_balance = None
                            if (new_balance and 'data' in new_balance and 'newBalance' in new_balance['data']
                                    and new_balance['data']['newBalance'] < 10):
                                current_timestamp = int(time.time())
                                data_append = {
                                    'transaction': 'money_record',
                                    'site': self.site_name,
                                    'time': current_timestamp,
                                    'money status': 'accepted',
                                    'money': response_money,
                                    'currency': '$',
                                    'money id': None
                                }
                                try:
                                    self.acc_history_collection.insert_one(data_append)
                                except:
                                    pass
                            if new_balance and 'message' in new_balance:
                                Logs.notify(self.tg_info,
                                            f"Balance Transfer: Invalid transfer: {new_balance['message']}", username)
                    except Exception as e:
                        Logs.notify_except(self.tg_info, f"Balance Transfer Global Error: {e}", username)
                    time.sleep(10)

    def database_csgo500(self):  # Global Function (class_for_account_functions)
        Logs.log(f"Database CSGO500: thread are running", '')
        while True:
            try:
                current_timestamp = int(time.time())
                try:
                    csgo500_doc = self.database_csgo500_collection.find_one()
                except:
                    csgo500_doc = None
                if csgo500_doc:
                    last_update_time = int(csgo500_doc.get("Time", 0))
                else:
                    last_update_time = 0

                difference_to_update = current_timestamp - last_update_time
                if difference_to_update > self.db_csgo500_validity_time:
                    try:
                        another_apis_list = self.search_in_merges_by_username(
                            self.steamclient.username)['csgo500 parse']
                    except:
                        another_apis_list = None
                    if another_apis_list:
                        another_api = random.choice(another_apis_list)
                        another_jwt_api_key = jwt.encode(
                            {'userId': another_api['user_id']},
                            another_api['apikey'],
                            algorithm="HS256"
                        )
                        another_csgo500_jwt_apikey = {'x-500-auth': another_jwt_api_key}
                        payload = {"pagination": {"referenceId": "",
                                                  "referenceFilterValue": 0,
                                                  "limit": 500,
                                                  "direction": "next"},
                                   "filters": {"appId": 730}}
                        counter = 0
                        data = {}
                        while counter < 1:
                            try:
                                search_url = f'{self.site_url}/api/v1/market/shop'
                                search_response = requests.post(search_url, headers=another_csgo500_jwt_apikey,
                                                                json=payload, timeout=15).json()
                                for item in search_response['data']['listings']:
                                    entry = {'site_item_id': item['id'], 'price': item['value']}
                                    if item['name'] in data:
                                        data[item['name']].append(entry)
                                    else:
                                        data[item['name']] = [entry]
                                if search_response.get('success') and len(search_response['data']['listings']) < 450:
                                    break
                                payload['pagination']["referenceId"] = search_response['data']['listings'][-1]['id']
                                payload['pagination']["referenceFilterValue"] = search_response[
                                    'data']['listings'][-1]['value']
                            except:
                                counter += 1

                            time.sleep(1)
                        csgo500_dict = {"Time": current_timestamp,
                                        "DataBaseCSGO500": data}
                        try:
                            self.database_csgo500_collection.replace_one({}, csgo500_dict, upsert=True)
                            Logs.log(f"Database CSGO500: DB Settings has been updated in MongoDB", '')

                        except Exception as e:
                            Logs.notify_except(self.tg_info,
                                               f"Database CSGO500: MongoDB critical request failed: {e}",
                                               '')
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Database CSGO500 Global Error: {e}", '')
            time.sleep(self.db_csgo500_global_time)
