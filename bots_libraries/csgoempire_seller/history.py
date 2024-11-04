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
                        try:
                            item_history_url = (f'{self.site_url}/api/v2/user/transactions?page=1'
                                                f'&per_page=100&type=deposits,tips,withdrawals')
                            response = requests.get(item_history_url, headers=self.csgoempire_headers,
                                                    timeout=15).json()
                            response_data = response['data']
                        except:
                            response_data = None
                        if response_data:
                            p2p_withdrawal = [item for item in response_data if item["type"] == "Steam P2P Deposit"]
                            tip = [item for item in response_data if item["type"] == "Tip"]
                            fees = [item for item in response_data if item["type"] == "Failed Auction Fee"]
                            self.site_history(p2p_withdrawal, history_docs)
                            self.money_history(tip, history_docs)
                            self.fee_history(fees, history_docs)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"History Global Error: {e}", self.steamclient.username)

    # region Site History
    def site_history(self, p2p_withdrawal, history_docs):
        try:
            current_timestamp = int(time.time())
            if p2p_withdrawal:
                history_docs_sorted = [
                    doc for doc in history_docs
                    if doc.get('site') == self.site_name
                    and doc.get('transaction') == 'sale_record'
                    and all(key in doc for key in ['site item id', 'site status', 'timestamp', 'asset id'])
                ]
                for doc in history_docs_sorted:
                    if doc["site status"] == 'active_deal':
                        match_for_alert = False
                        time_for_alert = False
                        for site_item in p2p_withdrawal:
                            if ('data' in site_item and 'metadata' in site_item['data']
                                    and 'item_id' in site_item['data']['metadata']
                                    and str(doc['site item id']) == str(site_item['data']['metadata']['item_id'])):
                                match_for_alert = True
                                if (current_timestamp - int(site_item['timestamp'])) <= 86400:
                                    time_for_alert = True

                                doc["site status"] = 'accepted'
                                doc['site status time'] = current_timestamp
                                try:
                                    rate = self.content_database_settings['DataBaseSettings']['CSGOEmpire_Seller'][
                                        'CSGOEmpire_Seller_rate']
                                except:
                                    rate = 0
                                if rate:
                                    hash_name = site_item['data']['metadata']['item']['market_name']
                                    site_price = round((int(site_item['delta']) / 100), 2)
                                    sold_price = round((site_price / rate), 3)

                                    self.send_sold_item_info(hash_name, site_price, sold_price,
                                                             'coins', 'coins', doc)
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

                        if not time_for_alert:
                            Logs.notify(self.tg_info, f"Site History: no trades in the last 24 hours",
                                        self.steamclient.username)
                self.site_history_new_docs(history_docs_sorted, p2p_withdrawal)

        except Exception as e:
            Logs.notify_except(self.tg_info, f"Site History Global Error: {e}", self.steamclient.username)
        time.sleep(3)

    def site_history_new_docs(self, history_docs_with_new_id, response_data):
        current_timestamp_unique = int(time.time())
        for site_item in response_data:
            if ('data' in site_item and 'metadata' in site_item['data'] and 'item_id' in site_item['data']['metadata']
                    and 'item' in site_item['data']['metadata'] and 'asset_id' in site_item['data']['metadata']['item']
                    and 'market_name' in site_item['data']['metadata']['item']):

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
                        "name": site_item['data']['metadata']['item']['market_name'],
                        "steam status": None,
                        "steam status time": None,
                        "site status": 'accepted',
                        "site status time": current_timestamp_unique,
                        "site id": None,
                        "buyer steam id": None,
                        "asset id": str(site_item['data']['metadata']['item']['asset_id']),
                        "trade id": None,
                        "sent time": None,
                        "site item id": str(site_item['data']['metadata']['item_id'])
                    }
                    try:
                        self.acc_history_collection.insert_one(data_append)
                    except:
                        pass
                    time.sleep(1)
    # endregion

    def money_history(self, tip, history_docs):
        try:
            for money_transfer in tip:
                if (all(key in money_transfer for key in ['data', 'delta'])
                        and 'id' in money_transfer['data']):
                    match = False
                    for doc in history_docs:
                        if 'money id' in doc and str(doc['money id']) == str(money_transfer['id']):
                            match = True
                            break

                    if not match:
                        money = abs(int(money_transfer['delta']) / 100)

                        current_timestamp = int(time.time())
                        data_append = {
                            'transaction': 'money_record',
                            'site': self.site_name,
                            'time': current_timestamp,
                            'money status': 'accepted',
                            'money': money,
                            'currency': 'coins',
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

    def fee_history(self, fees, history_docs):
        try:
            for fee in fees:
                if (all(key in fee for key in ['data', 'delta'])
                        and 'id' in fee['data']):
                    match = False
                    for doc in history_docs:
                        if 'fee id' in doc and str(doc['fee id']) == str(fee['id']):
                            match = True
                            break

                    if not match:
                        money = abs(int(fee['delta']) / 100)

                        Logs.notify(self.tg_info, f"Fee History: Fee on Item: {money}", self.steamclient.username)

                        current_timestamp = int(time.time())
                        data_append = {
                            "transaction": "fee_record",
                            "site": self.site_name,
                            "time": current_timestamp,
                            'money': money,
                            'currency': 'coins',
                            "site item id": str(fee['id'])
                        }

                        try:
                            self.acc_history_collection.insert_one(data_append)
                        except:
                            pass
                        time.sleep(1)
        except Exception as e:
            Logs.notify_except(self.tg_info, f"Fee History Global Error: {e}", self.steamclient.username)
        time.sleep(3)
    # endregion
