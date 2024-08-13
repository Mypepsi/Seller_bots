import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.thread_manager import ThreadManager


class TMHistory(ThreadManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region History
    def history(self, acc_info, tg_info, global_time):
        while True:
            try:
                time.sleep(global_time)
                self.update_account_data_info()
                self.update_db_prices_and_settings()
                active_session = self.take_session(acc_info, tg_info)
                if active_session:
                    collection_name = f'history_{self.steamclient.username}'
                    self.acc_history_collection = self.get_collection(self.history, collection_name)
                    collection_info = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
                    if collection_info:
                        self.steam_history('tm', collection_info, tg_info)
                        self.site_history(collection_info, tg_info)
                        self.money_history(collection_info, tg_info)
            except Exception as e:
                Logs.notify_except(tg_info, f"History Global Error: {e}", self.steamclient.username)

    # region Site History
    def site_history(self, collection_info, tg_info):
        try:
            current_timestamp = int(time.time())
            current_timestamp_unique = int(time.time())
            try:
                month_ago = current_timestamp - 30 * 24 * 60 * 60
                item_history_url = (f'{self.tm_url}/api/v2/history?key={self.tm_apikey}'
                                    f'&date={month_ago}&date_end={current_timestamp}')
                response = requests.get(item_history_url, timeout=30).json()
                response_info = response['data']
            except:
                response_info = None

            if response_info and isinstance(response_info, list):
                collection_info_sorted = [
                    doc for doc in collection_info
                    if doc.get('site') == 'tm'
                    and doc.get('transaction') == 'sale_record'
                    and all(key in doc for key in ['site item id', 'site status', 'asset id'])
                ]

                collection_info_with_new_id = self.search_site_item_id(tg_info, collection_info_sorted, response_info)

                for doc in collection_info_with_new_id:
                    if doc["site status"] == 'active_deal':
                        match_for_alert = False
                        for item_transfer in response_info:
                            if (all(key in item_transfer for key in ['item_id', 'stage', 'time'])
                                    and str(doc['site item id']) == str(item_transfer['item_id'])):
                                match_for_alert = True
                                stage = str(item_transfer['stage'])
                                if stage == '1':
                                    if (current_timestamp - int(item_transfer['time'])) >= 86400:
                                        Logs.notify_except(self.tm_tg_info, f"Site History: "
                                                                            f"'Active_deal' status on item with "
                                                                            f"{item_transfer['item_id']} itemID "
                                                                            f"more than 24 hours",
                                                           self.steamclient.username)
                                    break
                                elif stage == '2':
                                    doc["site status"] = 'accepted'
                                    doc['site status time'] = current_timestamp
                                    try:
                                        self.commission = self.content_database_settings['DataBaseSettings']['TM_Seller'][
                                            'TM_Seller_commission']
                                        self.rate = self.content_database_settings['DataBaseSettings']['TM_Seller'][
                                            'TM_Seller_rate']
                                    except:
                                        pass
                                    if self.commission and self.rate:
                                        hash_name = item_transfer['market_hash_name']
                                        site_price = round((int(item_transfer['received']) / 0.95 / 100), 2)
                                        sold_price = round((site_price / self.rate * self.commission), 3)
                                        currency = item_transfer["currency"]

                                        self.send_sold_item_info(self.tm_sale_price_bot_name, hash_name, site_price, sold_price,
                                                                 currency, '₽', doc,
                                                                 self.tm_history_tg_info, tg_info)

                                elif stage == '5':
                                    doc["site status"] = 'cancelled'
                                    doc['site status time'] = current_timestamp
                                else:
                                    doc["site status"] = 'unavailable'
                                    doc['site status time'] = current_timestamp
                                try:
                                    Logs.notify_except(self.tm_tg_info, f"'Unavailable' status on item with "
                                                                        f"{item_transfer['item_id']} itemID",
                                                       self.steamclient.username)
                                except Exception as e:
                                    Logs.notify_except(tg_info, f"Site History: MongoDB critical request failed: {e}",
                                                       self.steamclient.username)


                                self.acc_history_collection.update_one({'_id': doc['_id']}, {
                                    '$set': {'site status': doc['site status'], 'site status time': doc[
                                        'site status time']}})
                                time.sleep(1)
                                break

                        if not match_for_alert:
                            Logs.notify_except(tg_info, f"Site History: MongoDB {doc['site item id']} "
                                                        f"siteItemID not in site history", self.steamclient.username)
                for item_transfer in response_info:
                    if all(key in item_transfer for key in ['item_id', 'stage', 'time', 'market_hash_name', 'assetid']):

                        availability = False
                        for doc in collection_info_with_new_id:
                            if str(item_transfer['item_id']) == str(doc.get('site item id')):
                                availability = True
                                break

                        if not availability:
                            current_timestamp_unique += 1
                            data_append = {
                                "transaction": "sale_record",
                                "site": "tm",
                                "time": current_timestamp_unique,
                                "name": item_transfer['market_hash_name'],
                                "steam status": None,
                                "steam status time": None,
                                "site status": None,
                                "site status time": int(item_transfer['time']),
                                "site id": None,
                                "buyer steam id": None,
                                "asset id": None,
                                "trade id": None,
                                "sent time": None,
                                "site item id": str(item_transfer['item_id'])
                            }
                            stage = str(item_transfer['stage'])
                            if stage == '1':
                                if (current_timestamp - int(item_transfer['time'])) <= 86400:
                                    break
                                data_append["site status"] = 'active deal'
                            elif stage == '2':
                                data_append["site status"] = 'accepted'
                            elif stage == '5':
                                data_append["site status"] = 'cancelled'
                            else:
                                data_append["site status"] = 'unavailable'
                            try:
                                self.acc_history_collection.insert_one(data_append)
                            except Exception as e:
                                Logs.notify_except(tg_info, f"Site History: MongoDB critical request failed: {e}",
                                                   self.steamclient.username)
                            time.sleep(1)
        except Exception as e:
            Logs.notify_except(tg_info, f"Steam History Global Error: {e}", self.steamclient.username)

    def search_site_item_id(self, tg_info, collection_info_sorted, item_history_response_info):
        current_timestamp = int(time.time())
        collection_info_sorted_by_time = sorted(collection_info_sorted, key=lambda x: x.get('time', 0), reverse=True)

        for doc in collection_info_sorted_by_time:
            try:
                if doc['site item id'] is None:
                    list_of_matches = [
                        item_transfer
                        for item_transfer in item_history_response_info
                        if all(key in item_transfer for key in ['assetid', 'item_id', 'time'])
                        and not any(
                            str(inner_doc['site item id']) == str(item_transfer['item_id'])
                            for inner_doc in collection_info_sorted_by_time)
                        and str(doc['asset id']) == str(item_transfer['assetid'])
                    ]
                    closest_item_transfer = min(
                        (entry for entry in list_of_matches if int(entry['time']) <= current_timestamp),
                        key=lambda entry: current_timestamp - int(entry['time']),
                        default=None
                    )
                    if closest_item_transfer:
                        doc['site item id'] = str(closest_item_transfer['item_id'])
                        try:
                            self.acc_history_collection.update_one({'_id': doc['_id']},
                                                                   {'$set': {'site item id': doc['site item id']}})
                        except Exception as e:
                            Logs.notify_except(tg_info, f"Site History: MongoDB critical request failed: {e}",
                                               self.steamclient.username)
                        time.sleep(1)
                        for index, element in enumerate(collection_info_sorted_by_time):
                            if element.get('_id') == doc['_id']:
                                collection_info_sorted_by_time[index] = doc
                                break
            except:
                pass
        return collection_info_sorted_by_time
    # endregion

    def money_history(self, collection_info, tg_info):
        try:
            try:
                transfer_id = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_transfer_id']
                money_history_url = f'{self.tm_url}/api/v2/money-send-history/0?key={self.tm_apikey}'
                response = requests.get(money_history_url, timeout=30).json()
            except:
                transfer_id = None
                response = None

            if (transfer_id and response and 'success' in response and response['success'] is True
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
                                Logs.notify(tg_info, f"Money History: Strange {money_transfer['to']} transferID in "
                                                     f"{money_transfer['id']} transactionID", self.steamclient.username)
                            money = int(money_transfer['amount_from']) / 100

                            current_timestamp = int(time.time())
                            data_append = {
                                'transaction': 'money_record',
                                'site': 'tm',
                                'time': current_timestamp,
                                'money status': money_status,
                                'money': money,
                                'currency': money_transfer['currency_from'],
                                'money id': str(money_transfer['id'])

                            }
                            try:
                                self.acc_history_collection.insert_one(data_append)
                            except Exception as e:
                                Logs.notify_except(tg_info, f"Money History: MongoDB critical request failed: {e}",
                                                   self.steamclient.username)
                            time.sleep(1)
        except Exception as e:
            Logs.notify_except(tg_info, f"Money History Global Error: {e}", self.steamclient.username)
    # endregion