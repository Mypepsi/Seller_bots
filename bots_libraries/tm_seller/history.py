from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.thread_manager import ThreadManager
import time
import requests


class TMHistory(ThreadManager):
    def __init__(self):
        super().__init__()

    def history_check(self, acc_info, time_sleep):
        while True:
            time.sleep(time_sleep)
            self.update_account_data_info()
            self.update_db_prices_and_setting()
            username = acc_info['username']
            acc_data_phases_inventory = acc_info['steam inventory phases']
            steam_session = acc_info['steam session']
            self.take_session(steam_session)
            collection_name = f'history_{username}'
            self.acc_history_collection = self.get_collection(self.history, collection_name)
            collection_info = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
            if collection_info:
                try:
                    self.steam_history(collection_info)
                except:
                    Logs.log_and_send_msg_in_tg(self.tm_tg_info, 'Error in steam history', self.steamclient.username)

                try:
                    self.tm_item_history(collection_info, acc_data_phases_inventory)
                except:
                    Logs.log_and_send_msg_in_tg(self.tm_tg_info, 'Error in item history', self.steamclient.username)

                try:
                    self.tm_money_history(collection_info)
                except:
                    Logs.log_and_send_msg_in_tg(self.tm_tg_info, 'Error in money history', self.steamclient.username)
                time.sleep(30)

    def steam_history(self, collection_info):
        need_to_work = False
        for doc in collection_info:
            if 'steam status' in doc and doc['steam status'] in ['sent', 'again_sent', 'error_again_send']:
                need_to_work = True
                break
        if need_to_work:
            response = self.steamclient.get_trade_offers(self.steamclient.access_token, get_sent_offers=1,
                                                         get_received_offers=0, get_descriptions=0, active_only=0,
                                                         historical_only=0)

            if response and 'response' in response and 'trade_offers_sent' in response['response']:
                trade_offers = response['response']['trade_offers_sent']
                for doc in collection_info:
                    if ('steam status' in doc and doc['steam status'] in ['sent', 'again_sent', 'error_again_send']
                            and 'transaction' in doc and doc['transaction'] == 'sale_record'
                            and 'site' in doc and doc['site'] == 'tm'
                            and 'trade id' in doc and 'steam status time' in doc):
                        tradeofferid_alert = False

                        for offer in trade_offers:
                            if 'tradeofferid' in offer and offer['tradeofferid'] == doc['trade id']:
                                tradeofferid_alert = True

                                if ('asset id' in doc and 'items_to_give' in offer
                                        and not any(doc['asset id'] in item.values() for item in offer['items_to_give'])):

                                    Logs.log_and_send_msg_in_tg(self.tm_tg_info, f'Steam Trade History Bug: '
                                                                f'Mongo {doc["asset id"]} asset id not in '
                                                                f'{doc["trade id"]} trade id', self.steamclient.username)

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
                                    '$set': {'steam status': doc['steam status'], 'steam status time': doc[
                                        'steam status time']}})
                                time.sleep(1)

                        if not tradeofferid_alert:
                            Logs.log_and_send_msg_in_tg(self.tm_tg_info, f'Steam Trade History Bug: '
                                                        f'Mongo {doc["trade id"]} trade id not in steam trade history',
                                                        self.steamclient.username)

    def tm_item_history(self, collection_info, acc_data_phases_inventory):
        current_timestamp = int(time.time())
        current_timestamp_unique = int(time.time())
        month_ago = current_timestamp - 30*24*60*60
        item_history_url = (f'https://{self.tm_url}/api/v2/history?key={self.steamclient.tm_api}'
                            f'&date={month_ago}&date_end={current_timestamp}')
        try:
            response = requests.get(item_history_url, timeout=30).json()
            response_info = response['data']
        except:
            response = None
            response_info = None

        if response and response.get('success') and isinstance(response.get('data'), list):
            collection_info_sorted = [doc for doc in collection_info if doc.get('site') == 'tm'
                                      and doc.get('transaction') == 'sale record']
            collection_info_with_new_id = self.handling_empty_site_item_id(collection_info_sorted, response_info)
            for doc in collection_info_with_new_id:
                if all(key in doc for key in ['site item id', 'site status', 'site status time']):
                    if doc["site status"] == 'active deal':
                        match_for_alert = False

                        for item_transfer in response_info:
                            if (all(key in item_transfer for key in ['item_id', 'stage', 'time'])
                                    and doc['site item id'] == item_transfer['item_id']):
                                stage = item_transfer['stage']
                                match_for_alert = True

                                if stage == '1':
                                    if (current_timestamp - item_transfer['time']) >= 86400:
                                        Logs.log_and_send_msg_in_tg()
                                    continue
                                elif stage == '2':
                                    doc["site status"] = 'canceled'
                                    doc['site status time'] = current_timestamp
                                elif stage == '5':
                                    doc["site status"] = 'accepted'
                                    doc['site status time'] = current_timestamp
                                    hash_name = item_transfer['market_hash_name']
                                    try:
                                        self.commission = self.content_database_settings['DataBaseSettings']['TM_Seller'][
                                            'TM_Seller_commission']
                                        self.rate = self.content_database_settings['DataBaseSettings']['TM_Seller'][
                                            'TM_Seller_rate']
                                    except:
                                        pass
                                    site_price = round((int(item_transfer['received']) / 0.95 / 100), 2)
                                    sold_price = round((site_price / self.rate * self.commission), 3)

                                    currency = item_transfer["currency"]

                                    self.send_sold_item_info('tm_seller', hash_name, site_price, sold_price,
                                                                   acc_data_phases_inventory, currency, '₽', doc,
                                                                   self.tm_history_tg_info)

                                else:
                                    doc["site status"] = 'unavailable'
                                    doc['site status time'] = current_timestamp
                                    Logs.log_and_send_msg_in_tg(self.tm_tg_info, '', self.steamclient.username)
                                self.acc_history_collection.update_one({'_id': doc['_id']}, {
                                    '$set': {'site status': doc['site status'], 'site status time': doc[
                                        'site status time']}})
                                time.sleep(1)
                                break

                        if not match_for_alert:
                            Logs.log_and_send_msg_in_tg()

            for item_transfer in response_info:
                if all(key in item_transfer for key in ['item_id', 'stage', 'time', 'market_hash_name']):
                    for doc in collection_info_with_new_id:
                        if item_transfer['item_id'] == doc.get('site item id'):
                            current_timestamp_unique += 1
                            stage = item_transfer.get('stage')
                            data_append = {
                                "transaction": "sale_record",
                                "site": "tm",
                                "time": current_timestamp_unique,
                                "name": item_transfer['market_hash_name'],
                                "steam status": None,
                                "steam status time": None,
                                "site status": None,
                                "site status time": item_transfer['time'],
                                "site id": None,
                                "buyer steam id": None,
                                "asset id": None,
                                "trade id": None,
                                "sent time": None,
                                "site item id": item_transfer['item_id']
                            }
                            if stage == '1':
                                if (current_timestamp - item_transfer['time']) <= 86400:
                                    continue
                                data_append["site status"] = 'active deal'
                            elif stage == '2':
                                data_append["site status"] = 'canceled'
                            elif stage == '5':
                                data_append["site status"] = 'accepted'
                            else:
                                data_append["site status"] = 'unavailable'
                            self.acc_history_collection.insert_one(data_append)
                            time.sleep(1)

    def handling_empty_site_item_id(self, collection_info_sorted, item_history_response_info):
        current_timestamp = int(time.time())
        collection_info_sorted_by_time = sorted(collection_info_sorted, key=lambda x: x.get('time', 0), reverse=True)
        for doc in collection_info_sorted_by_time:
            try:
                if all(key in doc for key in ['site item id', 'name']) and doc['site item id'] is None:
                    match = False
                    for item_transfer in item_history_response_info:
                        keys_present = all(key in item_transfer for key in ['item_id', 'time', 'market_hash_name'])
                        if keys_present:
                            id_not_present = not any(
                                inner_doc['site item id'] == item_transfer['item_id'] for inner_doc in
                                collection_info_sorted_by_time)
                            if id_not_present:
                                match = True
                                break

                    if match:
                        list_of_matches = [
                            item_transfer for item_transfer in item_history_response_info
                            if 'item_id' in item_transfer and doc.get('name') == item_transfer['market_hash_name']
                        ]
                        closest_item_transfer = min(
                            (entry for entry in list_of_matches if int(entry['time']) <= current_timestamp),
                            key=lambda entry: current_timestamp - int(entry['time']),
                            default=None
                        )
                        if closest_item_transfer:
                            doc['site item id'] = closest_item_transfer['item_id']
                            self.acc_history_collection.update_one({'_id': doc['_id']},
                                                                   {'$set': {'site item id': closest_item_transfer[
                                                                       'item_id']}})
                            time.sleep(1)
                            for index, element in enumerate(collection_info_sorted_by_time):
                                if element.get('_id') == doc['_id']:
                                    collection_info_sorted_by_time[index] = doc
                                    break
            except:
                pass

        return collection_info_sorted_by_time


    def tm_money_history(self, collection_info):
        transfer_id = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_transfer_id']
        money_history_url = f'https://{self.tm_url}/api/v2/money-send-history/0?key={self.steamclient.tm_api}'
        try:
            response = requests.get(money_history_url, timeout=30).json()
        except:
            response = None
        try:
            if (response and 'success' in response and response['success'] is True
                    and 'data' in response and isinstance(response['data'], list)):
                for money_transfer in response['data']:
                    if all(key in money_transfer for key in ['id', 'to', 'amount_from', 'currency_from']):
                        match = False
                        money_status = 'accepted'
                        for doc in collection_info:
                            if 'money id' in doc and doc['money id'] == money_transfer['id']:
                                match = True
                                break

                        if not match:
                            if str(transfer_id) != str(money_transfer['to']):
                                money_status = 'error_strange_id'
                                text = f'Money History Bug: Strange Transfer: {money_transfer["id"]} transaction id'
                                Logs.log_and_send_msg_in_tg(self.tm_tg_info, text, self.steamclient.username)

                            current_timestamp = int(time.time())
                            data_append = {
                                'transaction': 'money_record',
                                'site': 'tm',
                                'time': current_timestamp,
                                'money status': money_status,
                                'money': int(money_transfer['amount_from']) / 100,
                                'currency': money_transfer['currency_from'],
                                'money id': money_transfer['id']

                            }
                            self.acc_history_collection.insert_one(data_append)
                            time.sleep(5)
        except Exception as e:
            Logs.log_and_send_msg_in_tg(self.tm_tg_info, f'Money History Bug: {e}', self.steamclient.username)
