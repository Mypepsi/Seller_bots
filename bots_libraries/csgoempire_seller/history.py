import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class CSGOEmpireHistory(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region History
    def history(self):  # Global Function (class_for_account_functions)
        while True:
            time.sleep(self.history_global_time)
            try:
                if self.active_session:
                    self.update_database_info(prices=True, settings=True)
                    history_docs = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
                    if history_docs:
                        self.steam_history(history_docs)
                        # self.site_history(history_docs)
                        # self.money_history(history_docs)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"History Global Error: {e}", self.steamclient.username)

    # region Site History
    def site_history(self, history_docs):
        try:
            current_timestamp = int(time.time())
            try:
                month_ago = current_timestamp - 30 * 24 * 60 * 60
                item_history_url = (f'{self.site_url}/api/v2/history?key={self.tm_apikey}'
                                    f'&date={month_ago}&date_end={current_timestamp}')
                response = requests.get(item_history_url, timeout=30).json()
                response_data = response['data']
            except:
                response_data = None

            if response_data and isinstance(response_data, list):
                history_docs_sorted = [
                    doc for doc in history_docs
                    if doc.get('site') == self.site_name
                    and doc.get('transaction') == 'sale_record'
                    and all(key in doc for key in ['site item id', 'site status', 'asset id'])
                ]

                history_docs_with_new_id = self.search_site_item_id(history_docs_sorted, response_data)

                for doc in history_docs_with_new_id:
                    if doc["site status"] == 'active_deal':
                        match_for_alert = False
                        for site_item in response_data:
                            if (all(key in site_item for key in ['item_id', 'stage'])
                                    and str(doc['site item id']) == str(site_item['item_id'])):
                                match_for_alert = True
                                stage = str(site_item['stage'])
                                if stage == '1':
                                    if (current_timestamp - int(site_item['time'])) >= 86400:
                                        Logs.notify(self.tg_info, f"Site History: "
                                                                            f"'Active_deal' status on item with "
                                                                            f"{site_item['item_id']} itemID "
                                                                            f"more than 24 hours",
                                                    self.steamclient.username)
                                    break
                                elif stage == '2':
                                    doc["site status"] = 'accepted'
                                    doc['site status time'] = current_timestamp
                                    try:
                                        commission = self.content_database_settings['DataBaseSettings']['TM_Seller'][
                                            'TM_Seller_commission']
                                        rate = self.content_database_settings['DataBaseSettings']['TM_Seller'][
                                            'TM_Seller_rate']
                                    except:
                                        rate = commission = 0
                                    if commission and rate:
                                        hash_name = site_item['market_hash_name']
                                        site_price = round((int(site_item['received']) / 0.95 / 100), 2)
                                        sold_price = round((site_price / rate * commission), 3)
                                        currency = site_item["currency"]

                                        self.send_sold_item_info(hash_name, site_price, sold_price,
                                                                 currency, '₽', doc)

                                elif stage == '5':
                                    doc["site status"] = 'cancelled'
                                    doc['site status time'] = current_timestamp
                                else:
                                    doc["site status"] = 'unavailable'
                                    doc['site status time'] = current_timestamp
                                    Logs.notify(self.tg_info,
                                                f"'Unavailable' status on item with {site_item['item_id']} itemID",
                                                self.steamclient.username)
                                try:
                                    self.acc_history_collection.update_one({'_id': doc['_id']},
                                                                           {'$set': {'site status': doc['site status'],
                                                                                     'site status time': doc['site status time']}})
                                except:
                                    pass
                                time.sleep(1)
                                break

                        if not match_for_alert:
                            Logs.notify(self.tg_info,
                                        f"Site History: MongoDB {doc['site item id']} siteItemID not in site history",
                                        self.steamclient.username)
                self.site_history_new_docs(history_docs_with_new_id, response_data)

        except Exception as e:
            Logs.notify_except(self.tg_info, f"Site History Global Error: {e}", self.steamclient.username)
        time.sleep(3)

    def site_history_new_docs(self, history_docs_with_new_id, response_data):
        current_timestamp_unique = current_timestamp = int(time.time())
        for site_item in response_data:
            if all(key in site_item for key in ['item_id', 'stage', 'time', 'market_hash_name', 'assetid']):

                availability = False
                for doc in history_docs_with_new_id:
                    if str(site_item['item_id']) == str(doc['site item id']):
                        availability = True
                        break

                if not availability:
                    current_timestamp_unique += 1
                    data_append = {
                        "transaction": "sale_record",
                        "site": self.site_name,
                        "time": current_timestamp_unique,
                        "name": site_item['market_hash_name'],
                        "steam status": None,
                        "steam status time": None,
                        "site status": None,
                        "site status time": int(site_item['time']),
                        "site id": None,
                        "buyer steam id": None,
                        "asset id": str(site_item['assetid']),
                        "trade id": None,
                        "sent time": None,
                        "site item id": str(site_item['item_id'])
                    }
                    stage = str(site_item['stage'])
                    if stage == '1':
                        if (current_timestamp - int(site_item['time'])) < 86400:
                            continue
                        data_append["site status"] = 'active deal'
                    elif stage == '2':
                        data_append["site status"] = 'accepted'
                    elif stage == '5':
                        data_append["site status"] = 'cancelled'
                    else:
                        data_append["site status"] = 'unavailable'
                    try:
                        self.acc_history_collection.insert_one(data_append)
                    except:
                        pass
                    time.sleep(1)
    # endregion

    def money_history(self, history_docs):
        try:
            try:
                transfer_id = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_transfer_id']
                money_history_url = f'{self.site_url}/api/v2/money-send-history/0?key={self.tm_apikey}'
                response = requests.get(money_history_url, timeout=30).json()
                response_money = response['data']
            except:
                transfer_id = None
                response_money = None

            if transfer_id and response_money and isinstance(response_money, list):
                for money_transfer in response_money:
                    if all(key in money_transfer for key in ['id', 'to', 'amount_from', 'currency_from']):
                        match = False
                        money_status = 'accepted'
                        for doc in history_docs:
                            if 'money id' in doc and str(doc['money id']) == str(money_transfer['id']):
                                match = True
                                break

                        if not match:
                            if str(transfer_id) != str(money_transfer['to']):
                                money_status = 'error_strange_id'
                                Logs.notify(self.tg_info, f"Money History: Strange {money_transfer['to']} transferID in "
                                                          f"{money_transfer['id']} transactionID", self.steamclient.username)
                            money = int(money_transfer['amount_from']) / 100

                            current_timestamp = int(time.time())
                            data_append = {
                                'transaction': 'money_record',
                                'site': self.site_name,
                                'time': current_timestamp,
                                'money status': money_status,
                                'money': money,
                                'currency': money_transfer['currency_from'],
                                'money id': str(money_transfer['id'])

                            }
                            try:
                                self.acc_history_collection.insert_one(data_append)
                            except:
                                pass
                            time.sleep(1)
        except Exception as e:
            Logs.notify_except(self.tg_info, f"Money History Global Error: {e}", self.steamclient.username)
        time.sleep(3)
    # endregion
