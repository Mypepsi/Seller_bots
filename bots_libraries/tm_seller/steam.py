import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.steampy.client import Asset
from bots_libraries.steampy.models import GameOptions
from bots_libraries.sellpy.thread_manager import ThreadManager



class TMSteam(ThreadManager):
    def __init__(self):
        super().__init__()
        self.commission = 0
        self.rate = 0

    #region steam send offers
    def request_give_p2p_all(self):
        try:
            url = f'https://{self.tm_url}/api/v2/trade-request-give-p2p-all?key={self.steamclient.tm_api}'
            response = requests.get(url, timeout=30).json()
            return response
        except:
            return None

    def make_steam_offer(self, response_data_offer, send_offers, inventory_phases):
        try:
            names = []
            assets = []
            assets_for_offer = []
            msg = response_data_offer['tradeoffermessage']
            for as_ in response_data_offer['items']:
                asset_id = as_['assetid']
                assets.append(asset_id)
                my_asset = Asset(str(asset_id), GameOptions.CS)
                assets_for_offer.append(my_asset)

            partner = response_data_offer['partner']
            token = response_data_offer['token']
            trade_offer_url = f'https://steamcommunity.com/tradeoffer/new/?partner={partner}&token={token}'
            try:
                creating_offer_time = int(time.time())
                steam_response = self.steamclient.make_offer_with_url(assets_for_offer, [], trade_offer_url, '')
                time.sleep(1)

                try:
                    self.steamclient.confirm_offer_via_tradeofferid(steam_response)
                except:
                    pass
                time.sleep(1)

                if steam_response is None or 'tradeofferid' not in steam_response:
                    trade_offer_id = self.check_created_trade(creating_offer_time, assets, partner)
                    steam_response = {'tradeofferid': trade_offer_id}
                else:
                    trade_offer_id = steam_response['tradeofferid']

                if trade_offer_id is not None:
                    self.handle_tm_history_doc(inventory_phases, send_offers, assets, names, msg,
                                               steam_response, trade_offer_url)
                    Logs.log(f"{self.steamclient.username}: Steam Trade Sent: {names}")
                else:
                    self.handle_tm_history_doc(inventory_phases, send_offers, assets, names, msg, None,
                                               trade_offer_url, success=False)
                    Logs.log(f"{self.steamclient.username}: Steam Trade Error to send: {names}")
            except Exception as e:
                Logs.log(f'Error when sending a steam trade: {e}')
        except Exception as e:
            Logs.log(f'Critical error during make steam offer: {e}')

    def check_created_trade(self, creating_offer_time, assets, partner):
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

    def handle_tm_history_doc(self, inventory_phases, send_offers, assets_list, name_list, msg, steam_response, offer_url,
                              success=True):
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
            for item in inventory_phases.values():
                if item['asset_id'] == asset:
                    name = item['market_hash_name']
                    name_list.append(name)
                    break
            name_exists = False
            trade_id_in_mongo = trade_id
            for entry in send_offers:
                if entry.get('site id') == msg:
                    trade_id_in_mongo = entry.get('trade id')
                    name_exists = True
                    break

            if name_exists:
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
                    self.acc_history_collection.update_one(
                        {
                            "$and": [
                                {"asset id": asset},
                                {"site id": msg}
                            ]
                        },
                        {
                            "$set": data
                        }
                    )
                else:
                    if trade_id_in_mongo is not None:
                        steam_status = 'error_again_send'
                        self.acc_history_collection.update_one(
                            {
                                "$and": [
                                    {"asset id": asset},
                                    {"site id": msg}
                                ]
                            },
                            {
                                "$set": {
                                    "steam status": steam_status,
                                    "steam status time": current_timestamp
                                }
                            }
                        )
            else:
                if sent_time is not None:
                    sent_time += 1
                current_timestamp_unique += 1
                partner_id = self.steamclient.return_partner_steam_id_from_url(offer_url)
                data_append = {
                    "transaction": "sale_record",
                    "site": "tm",
                    "time": current_timestamp_unique,
                    "name": name,
                    "steam status": steam_status,
                    "steam status time": current_timestamp_unique,
                    "site status": 'active_deal',
                    "site status time": current_timestamp_unique,
                    "site id": msg,
                    "buyer steam id": partner_id,
                    "asset id": asset,
                    "trade id": trade_id,
                    "sent time": sent_time,
                    "site item id": None
                }
                self.acc_history_collection.insert_one(data_append)

    def steam_send_offers(self, acc_info, time_sleep):
        while True:
            self.update_account_data_info()
            username = acc_info['username']
            acc_data_inventory_phases = acc_info['steam inventory phases']
            steam_session = acc_info['steam session']
            self.take_session(steam_session)
            collection_name = f'history_{username}'
            self.acc_history_collection = self.get_collection(self.history, collection_name)

            response_data = self.request_give_p2p_all()

            if ((self.acc_history_collection is not None and
                    response_data is not None and 'offers' in response_data
                    and type(response_data['offers']) == list)):
                send_offers = self.get_all_docs_from_mongo_collection(self.acc_history_collection)

                for i in range(len(response_data['offers'])):
                    try:
                        msg = response_data['offers'][i]['tradeoffermessage']
                        unique_msg_in_send_offers = []
                        trade_ready_list = []
                        for offer in send_offers:  # Trade ready:
                            try:
                                if 'site id' in offer:
                                    data_text = offer['site id']
                                    if msg == data_text:
                                        trade_ready_list.append(offer)
                            except:
                                pass
                        if len(trade_ready_list) > 0:
                            latest_offer = max(trade_ready_list, key=lambda t: t['time'])
                            trade_id = latest_offer['trade id']
                            if trade_id is not None:
                                trade_ready_url = (f'https://{self.tm_url}/api/v2/trade-ready?'
                                                   f'key={self.steamclient.tm_api}&tradeoffer={trade_id}')
                                try:
                                    requests.get(trade_ready_url, timeout=5)
                                except:
                                    pass
                                time.sleep(2)

                        match_msg = False
                        for offer in send_offers:
                            if 'site id' in offer and msg == offer['site id'] and offer['trade id'] is not None:
                                match_msg = True
                                break
                        if not match_msg:

                            self.make_steam_offer(response_data['offers'][i], send_offers, acc_data_inventory_phases)

                        for offer in send_offers:  # Resending and sending
                            if 'site id' in offer and msg == offer['site id'] and msg not in unique_msg_in_send_offers:
                                unique_msg_in_send_offers.append(msg)
                                trade_id = offer['trade id']
                                if trade_id is None:
                                    continue

                                response_steam_trade_offer = self.steamclient.get_trade_offer_state(trade_id)
                                time.sleep(2)

                                if not isinstance(response_steam_trade_offer, dict):
                                    continue

                                if 'response' in response_steam_trade_offer and 'offer' in response_steam_trade_offer['response']:
                                    offer_status = response_steam_trade_offer['response']['offer']['trade_offer_state']
                                else:
                                    continue

                                if int(offer_status) == 9:
                                    try:
                                        self.steamclient.confirm_offer_via_tradeofferid({'tradeofferid': trade_id})
                                    except:
                                        pass
                                    continue

                                if int(offer_status) not in [1, 4, 8, 10]:
                                    continue
                                self.make_steam_offer(response_data['offers'][i], send_offers, acc_data_inventory_phases)

                    except:
                        Logs.log('Error in steam send offers')
            elif self.acc_history_collection is not None and response_data is not None and 'error' in response_data:
                if response_data['error'] != 'nothing' and response_data['error'] != 'interval 45s':
                    Logs.log_and_send_msg_in_tg(self.tm_tg_info, 'Steam Send Offers: Error in '
                                                                 'trade-request-give-p2p-all', self.steamclient.username)
            time.sleep(time_sleep)

    # endregion
