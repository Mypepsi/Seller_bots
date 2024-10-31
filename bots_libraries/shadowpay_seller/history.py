import time
import requests
from datetime import datetime, timedelta
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class ShadowPayHistory(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region History
    def history(self):  # Global Function (class_for_account_functions)
        while True:
            # time.sleep(self.history_global_time)
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
                end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

                history_url = (f'{self.site_url}/api/v2/user/operations?token={self.shadowpay_apikey}'
                               f'&type=sell&date_from={start_date}&date_to={end_date}&limit=1000&offset=0'
                               f'&sort_column=time_created&sort_dir=desc')
                response = requests.get(history_url, timeout=15).json()
                trades = response['data']
            except:
                trades = None

            if trades and isinstance(trades, list):
                history_docs_sorted = [
                    doc for doc in history_docs
                    if doc.get('site') == self.site_name
                    and doc.get('transaction') == 'sale_record'
                    and all(key in doc for key in ['site item id', 'site status', 'asset id'])
                ]
                for doc in history_docs_sorted:
                    if doc["site status"] == 'active_deal':
                        match_for_alert = False
                        for site_item in trades:
                            if (all(key in site_item for key in ['id', 'state'])
                                    and str(doc['site item id']) == str(site_item['id'])):
                                state = str(site_item['state'])
                                match_for_alert = True
                                if state == 'active':
                                    if (current_timestamp - int(site_item['time'])) >= 86400:
                                        Logs.notify(self.tg_info, f"Site History: "
                                                                  f"'Active_deal' status on item with "
                                                                  f"{site_item['id']} itemID "
                                                                  f"more than 24 hours",
                                                    self.steamclient.username)
                                    break
                                elif state == 'finished':
                                    doc["site status"] = 'accepted'
                                    doc['site status time'] = current_timestamp
                                    try:
                                        commission = self.content_database_settings['DataBaseSettings'][
                                            'ShadowPay_Seller']['ShadowPay_Seller_commission']
                                    except:
                                        commission = 0
                                    if commission:
                                        hash_name = site_item['items']['steam_item']['steam_market_hash_name']
                                        site_price = round(site_item['price'], 2)
                                        sold_price = round((site_price * commission), 3)

                                        self.send_sold_item_info(hash_name, site_price, sold_price, '$', '$', doc)

                                elif state == 'cancelled':
                                    doc["site status"] = 'cancelled'
                                    doc['site status time'] = current_timestamp
                                else:
                                    doc["site status"] = 'unavailable'
                                    doc['site status time'] = current_timestamp
                                    Logs.notify(self.tg_info,
                                                f"'Unavailable' status on item with {site_item['id']} itemID",
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
                self.site_history_new_docs(history_docs_sorted, trades)

        except Exception as e:
            Logs.notify_except(self.tg_info, f"Site History Global Error: {e}", self.steamclient.username)
        time.sleep(3)

    def site_history_new_docs(self, history_docs_with_new_id, trades):
        current_timestamp_unique = current_timestamp = int(time.time())
        for site_item in trades:
            if ((all(key in site_item for key in ['id', 'state', 'asset_id'])) and 'items' in site_item and 'steam_item'
                    in site_item['items'] and 'steam_market_hash_name' in site_item['items']['steam_item']):

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
                        "name": site_item['items']['steam_item']['steam_market_hash_name'],
                        "steam status": None,
                        "steam status time": None,
                        "site status": None,
                        "site status time": current_timestamp_unique,
                        "site id": None,
                        "buyer steam id": None,
                        "asset id": str(site_item['id']),
                        "trade id": None,
                        "sent time": None,
                        "site item id": str(site_item['id'])
                    }
                    state = str(site_item['state'])
                    if state == 'active':
                        if (current_timestamp - int(site_item['time'])) < 86400:
                            continue
                        data_append["site status"] = 'active deal'
                    elif state == 'finished':
                        data_append["site status"] = 'accepted'
                    elif state == 'cancelled':
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
