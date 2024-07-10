from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.thread_manager import ThreadManager
import time
import requests


class TMHistory(ThreadManager):
    def __init__(self):
        super().__init__()


    def main_history(self, acc_info, time_sleep):
        while True:
            time.sleep(time_sleep)
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
            response = requests.get(item_history_url, timeout=30).json()
        except Exception as e:
            Logs.log(f"{self.steamclient.username}: Site History Bug: {e}")
            response = None

        if (response is not None and 'success' in response and response['success'] is True
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
            response = requests.get(money_history_url, timeout=30).json()
        except Exception as e:
            Logs.log(f"{self.steamclient.username}: Money History Bug: {e}")
            response = None
        if (response is not None and 'success' in response and response['success'] is True
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
