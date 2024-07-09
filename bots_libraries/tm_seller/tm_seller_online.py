from bots_libraries.base_info.logs import Logs, ExitException
from bots_libraries.creator.creator_steam import Steam
import math
import json
import time
import requests
import random
import urllib.parse


class TMOnline(Steam):
    def __init__(self):
        super().__init__()
        self.ping_alert = False
        self.history_steam_steam_status_alert = False
        self.history_steam_asset_id_alert = False

    def request_to_ping(self):
        try:
            url = f'https://market.csgo.com/api/v2/ping-new?key={self.steamclient.tm_api}'
            json_data = {
                'access_token': self.steamclient.access_token
            }
            if self.steamclient.proxies and 'http' in self.steamclient.proxies:
                json_data['proxy'] = self.steamclient.proxies['http']
            response = requests.post(url, json=json_data, timeout=20)
            if response.status_code == 200:
                response_data = response.json()
                if response_data['success'] is False and response_data['message'] != 'too early for ping':
                    Logs.log(f"{self.steamclient.username}: Ping Error: {response_data['message']}")
                    if not self.ping_alert:
                        self.tm_tg_bot.send_message(self.tm_tg_id,
                                                    f'TM Seller: Ping Error: {self.steamclient.username}')
                        self.ping_alert = True
        except:
            pass

    def ping(self, acc_info, time_sleep):
        username = ''
        while True:
            self.update_account_data_info()
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                self.request_to_ping()
            except:
                Logs.log(f'Error during take session in ping for {username}')
            time.sleep(time_sleep)

    def store_ping(self, acc_info, time_sleep):
        username = ''
        while True:
            self.update_account_data_info()
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                url = f'https://market.csgo.com/api/v2/go-offline?key={self.steamclient.tm_api}'

                try:
                    response = requests.get(url, timeout=20).json()
                except:
                    response = {}
                if 'success' in response and response['success'] is not True:
                    Logs.log(f'{username}: Offline Store Error')
            except:
                Logs.log(f'Error in store_ping for {username}')
            time.sleep(2)
            self.request_to_ping()
            time.sleep(time_sleep)

    def store_items_visible(self, acc_info, time_sleep):
        username = ''
        while True:
            time.sleep(time_sleep)
            search_result = False
            self.update_account_data_info()
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                try:
                    my_inventory_url = f'https://market.csgo.com/api/v2/my-inventory/?key={self.steamclient.tm_api}'
                    my_inventory_response = requests.get(my_inventory_url, timeout=20)
                    my_inventory_response_data = my_inventory_response.json()
                    my_inventory = my_inventory_response_data['items']
                except:
                    my_inventory = {}
                tradable_inventory = []
                for item in my_inventory:
                    if 'tradable' in item and item['tradable'] == 1:
                        tradable_inventory.append(item)
                if len(tradable_inventory) > self.tm_visible_store_num_of_items:
                    Logs.log(f'{username}: Not all items listed in Store')
                    self.tm_tg_bot.send_message(self.tm_tg_id,
                                                f'TM Seller: Not all items listed in Store: {username}')
                    raise ExitException

                items_url = f'https://market.csgo.com/api/v2/items?key={self.steamclient.tm_api}'
                response = requests.get(items_url, timeout=20)
                response_data = response.json()
                items_on_sale = response_data['items']
                if items_on_sale is not None and len(items_on_sale) != 0:
                    for _ in range(len(items_on_sale)):
                        random_item = random.choice(items_on_sale)
                        if random_item['status'] == '1':
                            hash_name = random_item['market_hash_name']
                            coded_hash_name = urllib.parse.quote(hash_name)
                            item_id = random_item['item_id']
                            another_tm_apis_list = self.search_in_merges_by_username(
                                self.steamclient.username)['tm apikey']
                            another_tm_api = random.choice(another_tm_apis_list)
                            search_url = (f'https://market.csgo.com/api/v2/search-list-items-by-hash-name-all?'
                                          f'key={another_tm_api}&extended=1&list_hash_name[]={coded_hash_name}')
                            search_response = requests.get(search_url, timeout=20)
                            search_response_data = search_response.json()
                            search_list = search_response_data['data'][hash_name]
                            for dictionary in search_list:
                                if 'id' in dictionary and str(dictionary['id']) == str(item_id):
                                    search_result = True
                                    break
                            if not search_result:
                                Logs.log(f'{username}: Store Visible Error')
                                self.tm_tg_bot.send_message(self.tm_tg_id,
                                                            f'TM Seller: Store Visible Error: {username}')
                                raise ExitException
            except ExitException:
                break
            except:
                Logs.log(f'{username}: Store items visible error')
        Logs.log(f'{username}: Thread store_items_visible was terminated')

    def validity_tm_apikey(self, time_sleep):
        while True:
            for acc_info in self.content_acc_list:
                try:
                    username = acc_info['username']
                    tm_api_key = acc_info['tm apikey']
                    balance_url = f'https://market.csgo.com/api/v2/get-money?key={tm_api_key}'
                    search_response = requests.get(balance_url, timeout=20)
                    search_response_data = search_response.json()
                    print(search_response_data)
                    if 'error' in search_response_data and search_response_data['error'] == 'Bad KEY':
                        Logs.log(f'{username}: TM API key Error')
                        self.tm_tg_bot.send_message(self.tm_tg_id, f'TM Seller: TM API key Error: {username}')
                except:
                    pass
                time.sleep(10)

            Logs.log(f'TM API key: All TM API key checked ({len(self.content_acc_list)} accounts in MongoDB)')
            time.sleep(time_sleep)

    def transfer_balance(self):
        api_to_withdraw = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_transfer_apikey']

        for acc in self.content_acc_list:
            try:
                username = acc['username']
                tm_api = acc['tm apikey']
                current_balance_url = f'https://market.csgo.com/api/v2/get-money?key={tm_api}'
                response = requests.get(current_balance_url, timeout=20)
                if response.status_code == 200:
                    data = json.loads(response.text)
                    money_value = data['money']
                    balance_tm = math.floor(money_value)
                    if balance_tm > 0:
                        time.sleep(3)
                        new_value = balance_tm * 100
                        withdrawing_tm_url = (f'https://market.csgo.com/api/v2/money-send/{new_value}/{api_to_withdraw}?'
                                              f'pay_pass=34368&key={tm_api}')
                        response = requests.get(withdrawing_tm_url, timeout=20)
                        if response.status_code == 200:
                            data = json.loads(response.text)
                            if 'amount' in data:
                                withdraw_money = data['amount'] / 100
                                Logs.log(f'{username}: {withdraw_money}: RUB transferred')
                            if 'error' in data and data['error'] == 'wrong_payment_password':
                                set_pay_password_url = (f'https://market.csgo.com/api/v2/set-pay-password?'
                                                        f'new_password=34368&key={tm_api}')
                                response = requests.get(set_pay_password_url)
                                if response.status_code == 200:
                                    data = json.loads(response.text)
                                    if 'success' in data and data['success']:
                                        Logs.log(f'{username}: payment password has been successfully set')
            except:
                pass

    def main_history(self, acc_info, time_sleep):

        while True:
            self.update_account_data_info()
            username = ''
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
            except:
                Logs.log('Error during taking a session')
            collection_name = f'history_{username}'
            collection_info = None
            try:
                self.acc_history_collection = self.get_collection(self.history, collection_name)
                collection_info = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
            except:
                Logs.log(f'Collecrion {collection_name} does not exist')
            if collection_info:
                self.steam_history(collection_info)
                self.tm_item_history(collection_info)
                self.tm_money_history(collection_info)

            time.sleep(time_sleep)

    def steam_history(self, collection_info):
        need_to_work = False
        for doc in collection_info:
            if 'steam status' in doc and doc['steam status'] in ['sent', 'again_sent', 'error_again_send']:
                need_to_work = True
                break

        if need_to_work:
            try:
                response = self.steamclient.get_trade_offers(self.steamclient.access_token, get_sent_offers=1,
                                                             get_received_offers=0, get_descriptions=0, active_only=0,
                                                             historical_only=0)
                trade_offers = response['response']['trade_offers_sent']
            except:
                trade_offers = []

            for doc in collection_info:
                if 'steam status' in doc and doc['steam status'] in ['sent', 'again_sent', 'error_again_send']:
                    found_in_trade_offers = False
                    for offer in trade_offers:
                        if 'tradeofferid' in offer and 'trade id' in doc and offer['tradeofferid'] == doc['trade id']:
                            found_in_trade_offers = True
                            break
                    if not found_in_trade_offers:
                        if not self.history_steam_steam_status_alert:
                            self.history_steam_steam_status_alert = True
                            Logs.log(f'{self.steamclient.username}: Trade  History Steam Bug: '
                                     f'steam_status not in steam request')
                            self.tm_tg_bot.send_message(self.tm_tg_id, f'TM Seller: '
                                                                       f'Trade  History Steam Bug: '
                                                                       f'{self.steamclient.username}: '
                                                                       f'steam_status not in steam request')

            for doc in collection_info:
                for offer in trade_offers:

                    if ('site' in doc and doc['site'] == 'tm'
                            and 'transaction' in doc and doc['transaction'] == 'sale_record'
                            and 'steam status' in doc and doc['steam status'] in ['sent', 'again_sent',
                                                                                  'error_again_send']
                            and 'tradeofferid' in offer and 'trade id' in doc
                        and 'steam status' in doc and 'steam status time' in doc
                            and offer['tradeofferid'] == doc['trade id']):

                        if ('asset id' in doc and 'items_to_give' in offer
                                and any(doc['asset id'] in item.values() for item in offer['items_to_give'])):
                            if 'trade_offer_state' in offer:
                                current_timestamp = int(time.time())
                                if offer['trade_offer_state'] in [2, 9]:
                                    continue
                                elif offer['trade_offer_state'] == 3:
                                    doc['steam status'] = 'accepted'
                                    doc['steam status time'] = current_timestamp
                                elif offer['trade_offer_state'] == 6:
                                    doc['steam status'] = 'canceled'
                                    doc['steam status time'] = current_timestamp
                                elif offer['trade_offer_state'] == 7:
                                    doc['steam status'] = 'declined'
                                    doc['steam status time'] = current_timestamp
                                else:
                                    doc['steam status'] = 'unavailable'
                                    doc['steam status time'] = current_timestamp
                                self.acc_history_collection.update_one({'_id': doc['_id']}, {
                                    '$set': {'steam status': doc['steam status'], 'steam status time': doc['steam status time']}})
                        else:
                            if not self.history_steam_asset_id_alert:
                                self.history_steam_asset_id_alert = True
                                Logs.log(f'{self.steamclient.username}: Trade  History Steam Bug: '
                                         f'asset_id not in steam request')
                                self.tm_tg_bot.send_message(self.tm_tg_id, f'TM Seller: '
                                                                           f'Trade  History Steam Bug: '
                                                                           f'{self.steamclient.username}: '
                                                                           f'asset_id not in steam request')

    def tm_item_history(self, collection_info):
        current_timestamp = int(time.time())
        item_history_url = (f'https://market.csgo.com/api/v2/history?key={self.steamclient.tm_api}'
                            f'&date_end={current_timestamp}')
        try:
            response = requests.get(item_history_url, timeout=20).json()
        except Exception as e:
            Logs.log(f"{self.steamclient.username}: Site History Bug: {e}")
            response = None

        if (response and 'success' in response and response['success'] is True
                and 'data' in response and isinstance(response['data'], list)):
            for item_transfer in response['data']:
                list_of_matches = []
                if all(key in item_transfer for key in ['item_id', 'market_hash_name', 'time']):
                    match = False
                    for doc in collection_info:
                        if doc['site item id'] == item_transfer['item_id']:
                            match = True
                            break
                    if not match:
                        for doc in collection_info:
                            if doc['site item id'] is None:
                                if doc['name'] == item_transfer['market_hash_name']:
                                    list_of_matches.append(item_transfer)
                        closest_item_transfer = None
                        closest_time_diff = float('inf')
                        for entry in list_of_matches:
                            entry_time = int(entry['time'])
                            if entry_time <= current_timestamp:
                                time_diff = current_timestamp - entry_time
                                if time_diff < closest_time_diff:
                                    closest_time_diff = time_diff
                                    closest_item_transfer = entry
                        for doc in collection_info:
                            if doc['site item id'] is None:
                                if doc['name'] == closest_item_transfer['market_hash_name']:
                                    doc['site item id'] = closest_item_transfer['item_id']
                                    if doc['site status'] == 'active deal' and closest_item_transfer['stage'] == '1':
                                        time_difference = current_timestamp - closest_item_transfer['time']
                                        if int(time_difference) >= 86400:
                                            self.tm_tg_bot.send_message(self.tm_tg_id,
                                                                        f'TM Seller: Site History Bug: '
                                                                        f'Too much difference between the record in '
                                                                        f'history and in Mongo:'
                                                                        f'{self.steamclient.username}')
                                            Logs.log(f'{self.steamclient.username}: Site History Bug: '
                                                     f'Too much difference between the record in history and in Mongo')
                                    elif doc['site status'] == 'active deal' and closest_item_transfer['stage'] == '2':
                                        doc['site status'] = 'canceled'
                                        doc['site status time'] = current_timestamp
                                    elif doc['site status'] == 'active deal' and closest_item_transfer['stage'] == '5':
                                        doc['site status'] = 'accepted'
                                        doc['site status time'] = current_timestamp
                                    else:
                                        self.tm_tg_bot.send_message(self.tm_tg_id,
                                                                    f'TM Seller: Site History Bug: Unknown status: '
                                                                    f'{self.steamclient.username}')
                                        Logs.log(f'{self.steamclient.username}: Site History Bug: Unknown status')

                                    self.acc_history_collection.update_one({'_id': doc['_id']}, {'$set': doc})
                    match_for_alert = False
                    if ('stage' in item_transfer and item_transfer['stage'] == '1'
                        and (current_timestamp - item_transfer['time']) >= 86400):
                        for doc in collection_info:
                            if doc['site item id'] == item_transfer['item_id']:
                                match_for_alert = True
                    if not match_for_alert:
                        status = None
                        if 'stage' in item_transfer and item_transfer['stage'] == '1':
                            status = 'active deal'
                        elif 'stage' in item_transfer and item_transfer['stage'] == '2':
                            status = 'canceled'
                        elif 'stage' in item_transfer and item_transfer['stage'] == '5':
                            status = 'accepted'
                            data_append = {
                                "transaction": "sale_record",
                                "site": "tm",
                                "time": current_timestamp,
                                "name": item_transfer['market_hash_name'],
                                "steam status": None,
                                "steam status time": None,
                                "site status": status,
                                "site status time": item_transfer['time'],
                                "site item id": None,
                                "site id": None,
                                "asset id": None,
                                "trade id": None,
                                "sent time": None
                            }
                            self.acc_history_collection.insert_one(data_append)

        for doc in collection_info:
            if (response and 'success' in response and response['success'] is True
                    and 'data' in response and isinstance(response['data'], list) and
                    doc['site status'] == 'active_deal'):
                match = False
                for item_transfer_ in response['data']:
                    if doc['site item id'] == item_transfer_['item_id']:
                        match = True
                        break
                if not match:
                    self.tm_tg_bot.send_message(self.tm_tg_id,
                                                f'TM Seller: Site History Bug: '
                                                f'Absence of a document from Mongo in history: '
                                                f'{self.steamclient.username}')
                    Logs.log(f'{self.steamclient.username}: Site History Bug: '
                             f'Absence of a document from Mongo in history')

    def tm_money_history(self, collection_info):
        money_history_url = f'https://market.csgo.com/api/v2/money-send-history/0?key={self.steamclient.tm_api}'
        try:
            response = requests.get(money_history_url, timeout=20).json()
        except Exception as e:
            Logs.log(f"{self.steamclient.username}: Money History Bug: {e}")
            response = None
        if (response and 'success' in response and response['success'] is True
                and 'data' in response and isinstance(response['data'], list)):
            current_timestamp = int(time.time())
            for money_transfer in response['data']:
                if all(key in money_transfer for key in ['id', 'amount_from', 'currency_from']):
                    match = False
                    for doc in collection_info:
                        if doc['money id'] == money_transfer['id']:
                            match = True
                            break
                    if not match:
                        data_append = {
                            'transaction': 'money_record',
                            'site': 'tm',
                            'time': current_timestamp,
                            'money status': 'accepted',
                            'money': money_transfer['amount_from'],
                            'currency': money_transfer['currency_from'],
                            'money id': money_transfer['id']

                        }
                        self.acc_history_collection.insert_one(data_append)



