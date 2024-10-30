import time
import requests
from datetime import datetime, timedelta
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class WaxpeerHistory(SteamManager):
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
                    self.site_history(history_docs)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"History Global Error: {e}", self.steamclient.username)

    # region Site History
    def site_history(self, history_docs):
        try:
            current_timestamp = int(time.time())
            try:
                end_date = (datetime.now() + timedelta(days=1)).strftime("%m-%d-%Y")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%m-%d-%Y")

                data = {"skip": 0,
                        "start": start_date,
                        "end": end_date}
                history_url = f'{self.site_url}/v1/my-history?api={self.waxpeer_apikey}'
                response = requests.post(history_url, data=data, timeout=15).json()
                trades = response['data']['trades']
            except:
                trades = None
            if trades and isinstance(trades, list):
                history_docs_sorted = [
                    doc for doc in history_docs
                    if doc.get('site') == self.site_name
                    and doc.get('transaction') == 'sale_record'
                    and all(key in doc for key in ['site item id', 'site status', 'asset id'])
                ]

                history_docs_with_new_id = self.search_site_item_id(history_docs_sorted, trades)

                for doc in history_docs_with_new_id:
                    if doc["site status"] == 'active_deal':
                        match_for_alert = False
                        for site_item in trades:
                            if (all(key in site_item for key in ['id', 'status'])
                                    and str(doc['site item id']) == str(site_item['id'])):
                                status = str(site_item['status'])
                                match_for_alert = True
                                if status in ['0', '2']:  # ще один добавити
                                    if (current_timestamp - int(site_item['time'])) >= 86400:
                                        Logs.notify(self.tg_info, f"Site History: "
                                                                  f"'Active_deal' status on item with "
                                                                  f"{site_item['item_id']} itemID "
                                                                  f"more than 24 hours",
                                                    self.steamclient.username)
                                    break
                                elif status == '5':
                                    doc["site status"] = 'accepted'
                                    doc['site status time'] = current_timestamp
                                    try:
                                        commission = self.content_database_settings['DataBaseSettings']['Waxpeer_Seller'][
                                            'Waxpeer_Seller_commission']
                                    except:
                                        commission = 0
                                    if commission:
                                        hash_name = site_item['name']
                                        site_price = round((int(site_item['price']) / 0.94 / 1000), 2)
                                        sold_price = round((site_price * commission), 3)

                                        self.send_sold_item_info(hash_name, site_price, sold_price, '$', '$', doc)

                                elif status == '6':
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
                self.site_history_new_docs(history_docs_with_new_id, trades)

        except Exception as e:
            Logs.notify_except(self.tg_info, f"Site History Global Error: {e}", self.steamclient.username)
        time.sleep(3)

    def search_site_item_id(self, history_docs_sorted, trades):
        current_timestamp = int(time.time())
        history_docs_sorted_by_time = sorted(history_docs_sorted, key=lambda x: x.get('time', 0), reverse=True)

        for doc in history_docs_sorted_by_time:
            try:
                if doc['site item id'] is None:
                    list_of_matches = [
                        site_item
                        for site_item in trades
                        if all(key in site_item for key in ['id', 'item_id', 'created'])
                        and str(doc['asset id']) == str(site_item['item_id'])
                        and not any(
                            str(inner_doc['site item id']) == str(site_item['id'])
                            for inner_doc in history_docs_sorted_by_time)
                    ]
                    for trade in list_of_matches:
                        trade["created"] = int(
                            time.mktime(datetime.strptime(trade["created"], "%Y-%m-%dT%H:%M:%S.%fZ").timetuple()))

                    closest_site_item = min(
                        (entry for entry in list_of_matches if int(entry['created']) <= current_timestamp),
                        key=lambda entry: current_timestamp - int(entry['created']),
                        default=None
                    )
                    if closest_site_item:
                        doc['site item id'] = str(closest_site_item['id'])
                        try:
                            self.acc_history_collection.update_one({'_id': doc['_id']},
                                                                   {'$set': {'site item id': doc['site item id']}})
                        except:
                            pass
                        time.sleep(1)
                        for index, element in enumerate(history_docs_sorted_by_time):
                            if element.get('_id') == doc['_id']:
                                history_docs_sorted_by_time[index] = doc
                                break
            except:
                pass
        return history_docs_sorted_by_time

    def site_history_new_docs(self, history_docs_with_new_id, trades):
        current_timestamp_unique = current_timestamp = int(time.time())
        for site_item in trades:
            if all(key in site_item for key in ['id', 'status', 'name', 'item_id']):

                availability = False
                for doc in history_docs_with_new_id:
                    if str(site_item['id']) == str(doc['site item id']):
                        availability = True
                        break

                if not availability:
                    current_timestamp_unique += 1
                    data_append = {
                        "transaction": "sale_record",
                        "site": self.site_name,
                        "time": current_timestamp_unique,
                        "name": site_item['name'],
                        "steam status": None,
                        "steam status time": None,
                        "site status": None,
                        "site status time": current_timestamp_unique,
                        "site id": None,
                        "buyer steam id": None,
                        "asset id": str(site_item['item_id']),
                        "trade id": None,
                        "sent time": None,
                        "site item id": str(site_item['id'])
                    }
                    status = str(site_item['status'])
                    if status in ['0', '2']:  # ще один
                        if (current_timestamp - int(site_item['time'])) < 86400:
                            continue
                        data_append["site status"] = 'active deal'
                    elif status == '5':
                        data_append["site status"] = 'accepted'
                    elif status == '6':
                        data_append["site status"] = 'cancelled'
                    else:
                        data_append["site status"] = 'unavailable'
                    try:
                        self.acc_history_collection.insert_one(data_append)
                    except:
                        pass
                    time.sleep(1)
    # endregion

    # endregion
