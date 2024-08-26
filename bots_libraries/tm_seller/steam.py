import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam
from bots_libraries.steampy.client import Asset
from bots_libraries.steampy.models import GameOptions


class TMSteam(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Steam Send Offers
    def steam_send_offers(self):
        while True:
            try:
                self.update_account_data_info()
                if self.active_session:
                    try:
                        url = f'{self.site_url}/api/v2/trade-request-give-p2p-all?key={self.tm_apikey}'
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
                                    trade_ready_url = (f'{self.site_url}/api/v2/trade-ready?'
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

                                self.make_steam_offer(request_site_offers['offers'][i], send_offers)

                            for offer in send_offers:  # Resending and sending
                                if 'site id' in offer and str(msg) == str(offer['site id']) and msg not in unique_msg_in_send_offers:
                                    unique_msg_in_send_offers.append(msg)
                                    trade_id = offer['trade id']
                                    if trade_id is None:
                                        break

                                    response_steam_trade_offer = self.steamclient.get_trade_offer_state(trade_id)
                                    time.sleep(1)

                                    if not isinstance(response_steam_trade_offer, dict):
                                        break

                                    if 'response' in response_steam_trade_offer and 'offer' in response_steam_trade_offer['response']:
                                        offer_status = response_steam_trade_offer['response']['offer']['trade_offer_state']
                                    else:
                                        break

                                    if int(offer_status) == 9:
                                        try:
                                            self.steamclient.confirm_trade_offer({'tradeofferid': trade_id})
                                        except:
                                            pass
                                        break

                                    if int(offer_status) not in [1, 4, 8, 10]:
                                        break
                                    self.make_steam_offer(request_site_offers['offers'][i], send_offers)
                                    break

            except Exception as e:
                Logs.notify_except(self.tg_info, f"Steam Send Offers Global Error: {e}", self.steamclient.username)
            time.sleep(self.steam_send_offers_global_time)

    def make_steam_offer(self, response_data_offer, send_offers):
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
            steam_response = self.steamclient.make_trade_offer(assets_for_offer, [], trade_offer_url)
            time.sleep(1)
            if steam_response is None or 'tradeofferid' not in steam_response:
                trade_offer_id = self.check_created_steam_offer(creating_offer_time, assets, partner)
                steam_response = {'tradeofferid': trade_offer_id}
            else:
                try:
                    self.steamclient.confirm_trade_offer(steam_response)
                except:
                    pass
                trade_offer_id = steam_response['tradeofferid']

            if trade_offer_id is not None:
                self.handle_doc_in_history(send_offers, assets, names, msg, steam_response, trade_offer_url)
                Logs.log(f"Make Steam Offer: Trade sent: {names}", self.steamclient.username)
            else:
                self.handle_doc_in_history(send_offers, assets, names, msg, steam_response, trade_offer_url,
                                           success=False)
                Logs.log(f"Make Steam Offer: Error send trade: {names}", self.steamclient.username)
        except Exception as e:
            Logs.notify_except(self.tg_info, f"Make Steam Offer Global Error: {e}", self.steamclient.username)

    def handle_doc_in_history(self, send_offers, assets_list, name_list, msg, steam_response,
                              offer_url, success=True):
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
                        Logs.notify_except(self.tg_info, f"Steam Send Offers: MongoDB critical request failed: {e}",
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
                            Logs.notify_except(self.tg_info, f"Steam Send Offers: MongoDB critical request failed: {e}",
                                               self.steamclient.username)
            else:
                if sent_time is not None:
                    sent_time += 1
                current_timestamp_unique += 1
                partner_id = self.steamclient.get_steamid_from_url(offer_url)
                data_append = {
                    "transaction": "sale_record",
                    "site": self.site_name,  # str
                    "time": current_timestamp_unique,  # int
                    "name": name,  # str
                    "steam status": steam_status,  # str
                    "steam status time": current_timestamp_unique,  # int
                    "site status": 'active_deal',
                    "site status time": current_timestamp_unique,  # int
                    "site id": str(msg),  # str
                    "buyer steam id": partner_id,  # i`m not sure)
                    "asset id": asset,  # str
                    "trade id": trade_id,  # str
                    "sent time": sent_time,  # int
                    "site item id": None
                }
                try:
                    self.acc_history_collection.insert_one(data_append)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Steam Send Offers: MongoDB critical request failed: {e}",
                                       self.steamclient.username)

    # endregion
