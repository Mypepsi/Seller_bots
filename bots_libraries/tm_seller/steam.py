from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.thread_manager import ThreadManager
from bots_libraries.steampy.models import GameOptions
from bots_libraries.steampy.client import Asset
import time
import requests



class TMSteam(ThreadManager):
    def __init__(self):
        super().__init__()
        self.commission = 0
        self.rate = 0

    #region tm sda
    def request_give_p2p_all(self):
        try:
            url = f'https://market.csgo.com/api/v2/trade-request-give-p2p-all?key={self.steamclient.tm_api}'
            response = requests.get(url, timeout=30)
            response_data = response.json()
            return response_data
        except Exception:
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
                steam_response = self.steamclient.make_offer_with_url(assets_for_offer, [], trade_offer_url, '')
                confirm_steam_response = self.steamclient.confirm_offer_via_tradeofferid(steam_response)
                time.sleep(3)
                if 'tradeofferid' in confirm_steam_response:
                    self.handle_tm_history_doc(inventory_phases, send_offers, assets, names, msg, confirm_steam_response)
                    Logs.log(f"{self.steamclient.username}: Steam Trade Sent: {names}")
                else:
                    Logs.log(f"{self.steamclient.username}: Steam Trade Error : {names}")
            except Exception as e:
                self.check_created_trade(assets_for_offer, partner)
                self.handle_tm_history_doc(inventory_phases, send_offers, assets, names, msg, None,
                                           success=False)
                Logs.log(f'Error when sending a steam trade: {e}')
        except Exception as e:
            Logs.log(f'Critical error during make steam offer: {e}')

    def check_created_trade(self, assets, partner):
        trade_offers = self.steamclient.get_trade_offers(self.steamclient.access_token, get_sent_offers=1,
                                                         get_received_offers=0, get_descriptions=0, active_only=0,
                                                         historical_only=0)
        if trade_offers and 'response' in trade_offers and 'trade_offers_sent' in trade_offers['response']:
            trade_offers_sent = trade_offers['response']['trade_offers_sent']

            matched_trades = []
            for offer in trade_offers_sent:
                time_created = offer['time_created']
                cursor = self.acc_history_collection.find({"trade id": offer['tradeofferid']})
                documents = list(cursor)
                if not documents:
                    return None
                latest_trade = max(documents, key=lambda doc: doc.get("time", float('-inf')))
                time_of_latest_trade = latest_trade.get("time")
                if time_created > time_of_latest_trade - 5:
                    if set(offer['items_to_give']) == set(assets) and offer['accountid_other'] == partner:
                        if not self.is_trade_in_mongo(offer['tradeofferid']):
                            matched_trades.append(offer)
            if matched_trades:
                latest_trade = max(matched_trades, key=lambda t: t['time_created'])  #шукає останій трейд в matched_trades
                if latest_trade['trade_offer_state'] == 9:
                    self.steamclient.confirm_offer_via_tradeofferid({'tradeofferid': latest_trade['tradeofferid']})

    def is_trade_in_mongo(self, tradeofferid) -> bool:
        return self.acc_history_collection.find_one({"trade id": tradeofferid}) is not None

    def handle_tm_history_doc(self, inventory_phases, send_offers, assets_list, name_list, msg, steam_response,
                              success=True):
        current_timestamp = int(time.time())
        time.sleep(1)
        if success:
            steam_status = 'sent'
            trade_id = steam_response['tradeofferid']
            sent_time = current_timestamp
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
            name_exists = any(entry.get('site id') == msg for entry in send_offers)

            if name_exists:
                if success:
                    steam_status = 'again_sent'
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
                                "steam status time": current_timestamp,
                                "site status time": current_timestamp,
                                "sent time": sent_time,
                                "trade id": trade_id
                            }
                        }
                    )
                else:
                    steam_status = 'error_again_sent'
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
                data_append = {
                    "transaction": "sale_record",
                    "site": "tm",
                    "time": current_timestamp,
                    "name": name,
                    "steam status": steam_status,
                    "steam status time": current_timestamp,
                    "site status": 'active_deal',
                    "site status time": current_timestamp,
                    "site item id": None,
                    "site id": msg,
                    "asset id": asset,
                    "trade id": trade_id,
                    "sent time": sent_time
                }
                self.acc_history_collection.insert_one(data_append)

    def tm_trades(self, acc_info, time_sleep):
        while True:
            self.update_account_data_info()
            acc_data_inventory_phases = []
            username = ''
            try:
                username = acc_info['username']
                acc_data_inventory_phases = acc_info['steam inventory phases']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
            except:
                Logs.log('Error during taking a session')
            collection_name = f'history_{username}'
            try:
                self.acc_history_collection = self.get_collection(self.history, collection_name)
            except:
                Logs.log(f'Collecrion {collection_name} does not exist')
            response_data = self.request_give_p2p_all()
            if response_data is not None and 'offers' in response_data and type(response_data['offers']) == list:
                send_offers = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
                for i in range(len(response_data['offers'])):
                    try:
                        msg = response_data['offers'][i]['tradeoffermessage']
                        unique_msg_in_send_offers = []
                        trade_ready_list = []
                        for offer in send_offers:  # Trade ready:
                            try:
                                data_text = offer['text']
                                if msg == data_text:
                                    trade_ready_list.append(offer)
                            except:
                                pass
                        if len(trade_ready_list) > 0:
                            latest_offer = max(trade_ready_list, key=lambda t: t['steam status time'])
                            trade_id = latest_offer['trade_id']
                            trade_ready_url = (f'https://market.csgo.com/api/v2/trade-ready?'
                                               f'key={self.steamclient.tm_api}&tradeoffer={trade_id}')
                            try:
                                requests.get(trade_ready_url, timeout=30)
                            except:
                                pass
                        for offer in send_offers:  # Resending
                            if msg in offer.values() and msg not in unique_msg_in_send_offers:
                                unique_msg_in_send_offers.append(msg)
                                trade_id = offer['trade id']
                                if trade_id is None:
                                    continue

                                response_steam_trade_offer = self.steamclient.get_trade_offer_state(trade_id)

                                if not isinstance(response_steam_trade_offer, dict):
                                    continue

                                if 'response' in response_steam_trade_offer and 'offer' in response_steam_trade_offer['response']:
                                    offer_status = response_steam_trade_offer['response']['offer']['trade_offer_state']
                                else:
                                    continue

                                if int(offer_status) == 9:
                                    self.steamclient.confirm_offer_via_tradeofferid({'tradeofferid': trade_id})
                                    continue

                                if int(offer_status) not in [1, 4, 8, 10]:
                                    continue

                            self.make_steam_offer(response_data['offers'][i], send_offers, acc_data_inventory_phases)
                    except:
                        Logs.log('Error in tm trades')
            elif 'error' in response_data:
                if response_data['error'] != 'nothing':
                    Logs.log(f"{self.steamclient.username}: {response_data['error']}")
            time.sleep(time_sleep)

    # endregion
