import time
import requests
from lxml import html
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class BuffHistory(SteamManager):
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
                headers = {'User-Agent': self.steamclient.user_agent}
                url = f'{self.site_url}/market/sell_order/history?game=csgo&page_num=1&page_size=100'
                response = requests.get(url, headers=headers, cookies=self.buff_cookie, timeout=15).text
                response_data = self.parsing_site_response(response)
            except:
                response_data = None

            if response_data:
                history_docs_sorted = [
                    doc for doc in history_docs
                    if doc.get('site') == self.site_name and doc.get('transaction') == 'sale_record'
                       and all(key in doc for key in ['site item id', 'site status', 'asset id'])
                ]

                history_docs_with_new_id = self.search_site_item_id(history_docs_sorted, response_data)
                for doc in history_docs_with_new_id:
                    if doc["site status"] == 'active_deal':
                        match_for_alert = False
                        for site_item in response_data:
                            status = site_item['status']
                            item_id = site_item['item_id']

                            if str(doc['site item id']) == str(item_id):
                                match_for_alert = True
                                if 'c_Blue' in status:
                                    if (current_timestamp - int(site_item['time'])) >= 86400:
                                        Logs.notify(self.tg_info, f"Site History: "
                                                                  f"'Active_deal' status on item with "
                                                                  f"{item_id} itemID "
                                                                  f"more than 24 hours",
                                                    self.steamclient.username)
                                    break
                                elif 'c_Green' in status:
                                    doc["site status"] = 'accepted'
                                    doc['site status time'] = current_timestamp

                                    try:
                                        commission = self.content_database_settings['DataBaseSettings'][
                                            'Buff_Seller']['Buff_Seller_commission']
                                        rate = self.content_database_settings['DataBaseSettings'][
                                            'Buff_Seller']['Buff_Seller_rate']
                                    except:
                                        rate = commission = 0
                                    if commission and rate:
                                        site_price = round(site_item['price'], 2)
                                        sold_price = round((site_price / rate * commission), 3)

                                        self.send_sold_item_info(site_item['market_hash_name'], site_price, sold_price,
                                                                 '¥', '¥', doc)

                                elif 'c_Red' in status:
                                    doc["site status"] = 'cancelled'
                                    doc['site status time'] = current_timestamp
                                else:
                                    doc["site status"] = 'unavailable'
                                    doc['site status time'] = current_timestamp
                                    Logs.notify(self.tg_info,
                                                f"'Unavailable' status on item with {item_id} itemID",
                                                self.steamclient.username)
                                try:
                                    self.acc_history_collection.update_one({'_id': doc['_id']},
                                                                           {'$set': {'site status': doc[
                                                                               'site status'],
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
                self.site_history_new_docs(history_docs_with_new_id, response_data)

        except Exception as e:
            Logs.notify_except(self.tg_info, f"Site History Global Error: {e}", self.steamclient.username)

    @staticmethod
    def parsing_site_response(response):
        current_timestamp = int(time.time())
        parsed_body = html.fromstring(response)
        items_raw = parsed_body.xpath("//tbody[@class='list_tb_csgo']/tr")

        items = []

        for item in items_raw:
            try:
                unix_time = int(item.xpath(".//td[@class='c_Gray t_Left']/span[@class='moment-ts']/@data-ts")[0])
                if (current_timestamp - unix_time) < 5 * 86400:
                    asset_id = item.xpath(".//div[@class='pic-cont item-detail-img']/@data-assetid")[0]

                    market_hash_name = item.xpath(".//span[@class='textOne']/text()")[0]

                    status = item.xpath(".//td[@class='t_Left deliver-expire td_status td_status--p2p']/div/@class")[0]

                    price_main = item.xpath(".//td")[3].xpath(".//strong/text()")[0]
                    price_fraction = item.xpath(".//td")[3].xpath(".//small/text()")[0]
                    price = float((price_main + price_fraction).replace("¥", "").strip())

                    item_id = item.xpath(".//div[@class='c_Gray j_drop-handler j_copy_handler']/@data")[0]

                    items.append({'asset_id': asset_id,
                                  'market_hash_name': market_hash_name,
                                  'status': status,
                                  'price': price,
                                  'time': unix_time,
                                  'item_id': item_id})
            except:
                pass
        return items

    def search_site_item_id(self, history_docs_sorted, trades):
        current_timestamp = int(time.time())
        history_docs_sorted_by_time = sorted(history_docs_sorted, key=lambda x: x.get('time', 0), reverse=True)

        for doc in history_docs_sorted_by_time:
            try:
                if doc['site item id'] is None:
                    list_of_matches = [
                        item
                        for item in trades
                        if all(key in item for key in ['item_id', 'asset_id'])
                        and str(doc['asset id']) == str(item['asset_id'])
                        and not any(
                            str(inner_doc['site item id']) == str(item['item_id'])
                            for inner_doc in history_docs_sorted_by_time)
                    ]

                    closest_site_item = min(
                        (entry for entry in list_of_matches if int(entry['time']) <= current_timestamp),
                        key=lambda entry: current_timestamp - int(entry['time']),
                        default=None
                    )
                    if closest_site_item:
                        doc['site item id'] = str(closest_site_item['item_id'])
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

    def site_history_new_docs(self, history_docs_with_new_id, response_data):
        current_timestamp_unique = current_timestamp = int(time.time())
        for site_item in response_data:
            item_id = site_item['item_id']

            availability = False
            for doc in history_docs_with_new_id:
                if str(item_id) == str(doc['site item id']):
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
                    "asset id": str(site_item['asset_id']),
                    "trade id": None,
                    "sent time": None,
                    "site item id": str(item_id)
                }

                status = site_item['status']
                if 'c_Blue' in status:
                    if (current_timestamp - int(site_item['time'])) < 86400:
                        continue
                    data_append["site status"] = 'active deal'
                elif 'c_Green' in status:
                    data_append["site status"] = 'accepted'
                elif 'c_Red' in status:
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
