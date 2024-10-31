import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class CSGO500History(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.dispute_id_list = []

    # region History
    def history(self):  # Global Function (class_for_account_functions)
        while True:
            # time.sleep(self.history_global_time)
            try:
                print(self.active_session)
                if self.active_session:
                    self.update_database_info(prices=True, settings=True)
                    history_docs = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
                # if history_docs:
                    self.steam_history(history_docs)
                    self.site_history(history_docs)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"History Global Error: {e}", self.steamclient.username)

    # region Site History
    def site_history(self, history_docs):
        try:
            current_timestamp = int(time.time())
            try:
                item_history_url = (f'{self.site_url}/api/v1/market/listings/deposit/finished'
                                    f'?appId=730&page=1&sort=date-desc')
                response = requests.get(item_history_url, headers=self.csgo500_jwt_apikey, timeout=15).json()
                response_data = response['data']['listings']
            except:
                response_data = None
            print(response_data)
            if response_data and isinstance(response_data, list):
                history_docs_sorted = [
                    doc for doc in history_docs
                    if doc.get('site') == self.site_name
                       and doc.get('transaction') == 'sale_record'
                       and all(key in doc for key in ['site item id', 'site status', 'asset id'])
                ]
                for doc in history_docs_sorted:
                    if doc["site status"] == 'active_deal':
                        match_for_alert = False
                        for site_item in response_data:
                            if (all(key in site_item for key in ['id', 'shortStatus'])
                                    and str(doc['site item id']) == str(site_item['id'])):
                                match_for_alert = True
                                short_status = str(site_item['shortStatus'])
                                if short_status == 'market_disputed':
                                    if site_item['id'] not in self.dispute_id_list:
                                        price = int(site_item['value']) / 1000
                                        Logs.notify(self.tg_info, f"Active Dispute: \n{site_item['name']}\n"
                                                                  f"Site Price: {price} coins\n"
                                                                  f"ID: {site_item['id']}", self.steamclient.username)
                                        self.dispute_id_list.append(site_item['id'])
                                    break
                                elif short_status == 'market_accepted':
                                    doc["site status"] = 'accepted'
                                    doc['site status time'] = current_timestamp
                                    try:
                                        rate = self.content_database_settings['DataBaseSettings']['CSGO500_Seller'][
                                            'CSGO500_Seller_rate']
                                    except:
                                        rate = 0
                                    if rate:
                                        hash_name = site_item['market_hash_name']
                                        site_price = round((int(site_item['value']) / 1000), 2)
                                        sold_price = round((int(site_item['value']) / rate), 3)

                                        self.send_sold_item_info(hash_name, site_price, sold_price, 'coins', 'coins',
                                                                 doc)

                                elif short_status == 'market_cancelled':
                                    doc["site status"] = 'cancelled'
                                    doc['site status time'] = current_timestamp
                                else:
                                    doc["site status"] = 'unavailable'
                                    doc['site status time'] = current_timestamp
                                    Logs.notify(self.tg_info,
                                                f"'Unavailable' status on item with {site_item['id']} ID",
                                                self.steamclient.username)
                                try:
                                    self.acc_history_collection.update_one({'_id': doc['_id']},
                                                                           {'$set': {'site status': doc['site status'],
                                                                                     'site status time': doc[
                                                                                         'site status time']}})
                                except:
                                    pass
                                time.sleep(1)
                                break

                        if not match_for_alert:
                            Logs.notify(self.tg_info,
                                        f"Site History: MongoDB {doc['site item id']} siteItemID not in site history",
                                        self.steamclient.username)
                self.site_history_new_docs(history_docs_sorted, response_data)

        except Exception as e:
            Logs.notify_except(self.tg_info, f"Site History Global Error: {e}", self.steamclient.username)
        time.sleep(3)

    def site_history_new_docs(self, history_docs_with_new_id, response_data):
        current_timestamp_unique = int(time.time())
        for site_item in response_data:
            if all(key in site_item for key in ['id', 'shortStatus', 'name', 'assetId']):

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
                        "name": site_item['market_hash_name'],
                        "steam status": None,
                        "steam status time": None,
                        "site status": None,
                        "site status time": current_timestamp_unique,
                        "site id": None,
                        "buyer steam id": None,
                        "asset id": str(site_item['assetId']),
                        "trade id": None,
                        "sent time": None,
                        "site item id": str(site_item['id'])
                    }
                    short_status = str(site_item['shortStatus'])
                    if short_status == 'market_disputed':
                        data_append["site status"] = 'disputed'
                    elif short_status == 'market_accepted':
                        data_append["site status"] = 'accepted'
                    elif short_status == 'market_cancelled':
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
