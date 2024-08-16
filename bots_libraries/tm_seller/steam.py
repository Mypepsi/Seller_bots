import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.steampy.client import Asset
from bots_libraries.steampy.models import GameOptions
from bots_libraries.sellpy.thread_manager import ThreadManager


class TMSteam(ThreadManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Steam Send Offers
    def steam_send_offers(self, acc_info, tg_info, global_time):
        while True:
            try:
                self.update_account_data_info()
                active_session = self.take_session(acc_info, tg_info)
                if active_session:
                    collection_name = f'history_{self.steamclient.username}'
                    self.acc_history_collection = self.get_collection(self.history, collection_name)
                    try:
                        url = f'{self.tm_url}/api/v2/trade-request-give-p2p-all?key={self.tm_apikey}'
                        request_site_offers = requests.get(url, timeout=30).json()
                    except:
                        request_site_offers = None

                    if (request_site_offers and 'offers' in request_site_offers
                            and type(request_site_offers['offers']) == list):
                        send_offers = self.get_all_docs_from_mongo_collection(self.acc_history_collection)

                        for i in range(len(request_site_offers['offers'])):
                            msg = request_site_offers['offers'][i]['tradeoffermessage']
                            unique_msg_in_send_offers = []
                            trade_ready_list = []
                            for offer in send_offers:  # Trade ready:
                                try:
                                    if 'site id' in offer:
                                        data_text = str(offer['site id'])
                                        if msg == data_text:
                                            trade_ready_list.append(offer)
                                except:
                                    pass
                            if len(trade_ready_list) > 0:
                                latest_offer = max(trade_ready_list, key=lambda t: t['time'])
                                trade_id = latest_offer['trade id']
                                if trade_id is not None:
                                    trade_ready_url = (f'{self.tm_url}/api/v2/trade-ready?'
                                                       f'key={self.tm_apikey}&tradeoffer={trade_id}')
                                    try:
                                        requests.get(trade_ready_url, timeout=5)
                                    except:
                                        pass
                                    time.sleep(3)

                            match_msg = False
                            for offer in send_offers:
                                if 'site id' in offer and str(msg) == str(offer['site id']) and offer['trade id'] is not None:
                                    match_msg = True
                                    break
                            if not match_msg:

                                self.make_steam_offer(request_site_offers['offers'][i], send_offers, tg_info)

                            for offer in send_offers:  # Resending and sending
                                if 'site id' in offer and str(msg) == str(offer['site id']) and msg not in unique_msg_in_send_offers:
                                    unique_msg_in_send_offers.append(msg)
                                    trade_id = offer['trade id']
                                    if trade_id is None:
                                        break

                                    response_steam_trade_offer = self.steamclient.get_trade_offer_state(trade_id)
                                    time.sleep(3)

                                    if not isinstance(response_steam_trade_offer, dict):
                                        break

                                    if 'response' in response_steam_trade_offer and 'offer' in response_steam_trade_offer['response']:
                                        offer_status = response_steam_trade_offer['response']['offer']['trade_offer_state']
                                    else:
                                        break

                                    if int(offer_status) == 9:
                                        try:
                                            self.steamclient.confirm_offer_via_tradeofferid({'tradeofferid': trade_id})
                                        except:
                                            pass
                                        break

                                    if int(offer_status) not in [1, 4, 8, 10]:
                                        break
                                    self.make_steam_offer(request_site_offers['offers'][i], send_offers, tg_info)
                                    break

            except Exception as e:
                Logs.notify_except(tg_info, f"Steam Send Offers Global Error: {e}", self.steamclient.username)
            time.sleep(global_time)

    def make_steam_offer(self, response_data_offer, send_offers, tg_info):
        try:
            names = []
            assets = []
            assets_for_offer = []
            msg = response_data_offer['tradeoffermessage']
            partner = response_data_offer['partner']
            token = response_data_offer['token']
            for item in response_data_offer['items']:
                asset_id = item['assetid']
                assets.append(asset_id)
                my_asset = Asset(str(asset_id), GameOptions.CS)
                assets_for_offer.append(my_asset)

            trade_offer_url = f'https://steamcommunity.com/tradeoffer/new/?partner={partner}&token={token}'
            creating_offer_time = int(time.time())
            steam_response = self.steamclient.make_offer_with_url(assets_for_offer, [], trade_offer_url, '')
            time.sleep(1)

            if steam_response is None or 'tradeofferid' not in steam_response:
                trade_offer_id = self.check_created_steam_offer(creating_offer_time, assets, partner)
                steam_response = {'tradeofferid': trade_offer_id}
            else:
                try:
                    self.steamclient.confirm_offer_via_tradeofferid(steam_response)
                    time.sleep(1)
                except:
                    pass
                trade_offer_id = steam_response['tradeofferid']

            if trade_offer_id is not None:
                self.handle_doc_in_history(send_offers, assets, names, msg, steam_response, trade_offer_url, tg_info)
                Logs.log(f"Make Steam Offer: Trade sent: {names}", self.steamclient.username)
            else:
                self.handle_doc_in_history(send_offers, assets, names, msg, None, trade_offer_url, tg_info,
                                           success=False)
                Logs.log(f"Make Steam Offer: Error send trade: {names}", self.steamclient.username)
        except Exception as e:
            Logs.notify_except(tg_info, f"Make Steam Offer Global Error: {e}", self.steamclient.username)

    def check_created_steam_offer(self, creating_offer_time, assets, partner):
        trade_offers = self.steamclient.get_trade_offers(self.steamclient.access_token, get_sent_offers=1,
                                                         get_received_offers=0, get_descriptions=0, active_only=0,
                                                         historical_only=0)
        if (trade_offers
                and trade_offers and 'response' in trade_offers and 'trade_offers_sent' in trade_offers['response']):
            trade_offers_sent = trade_offers['response']['trade_offers_sent']
            history_docs = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
            matched_trades = []
            for offer in trade_offers_sent:
                try:
                    time_created = offer['time_created']
                    match = False
                    for doc in history_docs:
                        if "trade id" in doc and doc["trade id"] == offer['tradeofferid']:
                            match = True
                            break
                    if match:
                        continue
                    if time_created > creating_offer_time - 15:
                        asset_id_from_trade_offers = [item['assetid'] for item in offer['items_to_give']]
                        if set(asset_id_from_trade_offers) == set(assets) and offer['accountid_other'] == partner:
                            matched_trades.append(offer)
                except:
                    pass
            if matched_trades:
                latest_trade_steam = max(matched_trades, key=lambda t: t['time_created'])
                if latest_trade_steam['trade_offer_state'] == 9:
                    try:
                        self.steamclient.confirm_offer_via_tradeofferid({'tradeofferid': latest_trade_steam['tradeofferid']})
                    except:
                        pass
                return latest_trade_steam['tradeofferid']
            else:
                return None
        else:
            return None

    def handle_doc_in_history(self, send_offers, assets_list, name_list, msg, steam_response,
                              offer_url, tg_info, success=True):
        current_timestamp = int(time.time())
        current_timestamp_unique = int(time.time())
        if success:
            steam_status = 'sent'
            trade_id = steam_response['tradeofferid']
            sent_time = current_timestamp_unique
        else:
            steam_status = 'error_send'
            trade_id = None
            sent_time = None

        for asset in assets_list:
            name = ''
            doc_exist = False
            trade_id_in_mongo = trade_id
            for entry in send_offers:
                if str(entry.get('site id')) == str(msg):
                    trade_id_in_mongo = entry.get('trade id')
                    doc_exist = True
                    break
            for item in self.steam_inventory_phases.values():
                if item['asset_id'] == asset:
                    name = item['market_hash_name']
                    name_list.append(name)
                    break
            if doc_exist:
                data = {
                    "steam status time": current_timestamp,
                    "trade id": trade_id
                }
                if success:
                    if trade_id_in_mongo is not None:
                        data['steam status'] = 'again_sent'
                    else:
                        data['steam status'] = 'sent'
                        data['sent time'] = current_timestamp
                    try:
                        self.acc_history_collection.update_one(
                            {
                                "$and": [
                                    {"asset id": asset},
                                    {"site id": str(msg)}
                                ]
                            },
                            {
                                "$set": data
                            }
                        )
                    except Exception as e:
                        Logs.notify_except(tg_info, f"Steam Send Offers: MongoDB critical request failed: {e}",
                                           self.steamclient.username)
                else:
                    if trade_id_in_mongo is not None:
                        steam_status = 'error_again_send'
                        try:
                            self.acc_history_collection.update_one(
                                {
                                    "$and": [
                                        {"asset id": asset},
                                        {"site id": str(msg)}
                                    ]
                                },
                                {
                                    "$set": {
                                        "steam status": steam_status,
                                        "steam status time": current_timestamp
                                    }
                                }
                            )
                        except Exception as e:
                            Logs.notify_except(tg_info, f"Steam Send Offers: MongoDB critical request failed: {e}",
                                               self.steamclient.username)
            else:
                if sent_time is not None:
                    sent_time += 1
                current_timestamp_unique += 1
                partner_id = self.steamclient.return_partner_steam_id_from_url(offer_url)
                data_append = {
                    "transaction": "sale_record",
                    "site": "tm",  # str
                    "time": current_timestamp_unique,  # int
                    "name": name,  # str
                    "steam status": steam_status,  # str
                    "steam status time": current_timestamp_unique,  # int
                    "site status": 'active_deal',
                    "site status time": current_timestamp_unique,  # int
                    "site id": str(msg),  # str
                    "buyer steam id": partner_id,  # i`m not sure)
                    "asset id": asset,  # str
                    "trade id": trade_id,  # ??? i`m not sure)
                    "sent time": sent_time,  # int
                    "site item id": None
                }
                try:
                    self.acc_history_collection.insert_one(data_append)
                except Exception as e:
                    Logs.notify_except(tg_info, f"Steam Send Offers: MongoDB critical request failed: {e}",
                                       self.steamclient.username)

    # endregion
