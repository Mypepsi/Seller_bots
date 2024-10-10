import time
import json
import requests
import websocket
import threading
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.steampy.client import SteamClient


class ShadowPaySteam(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.site_offers_send = []
        self.site_offers_cancel = []
        self.site_offers_cancelled = []
        self.ws = websocket.WebSocket()
        self.active_socket = False

    # region Steam Send Offers
    def steam_send_offers(self):  # Global Function (class_for_account_functions)
        threading.Thread(target=self.site_socket).start()
        while True:
            try:
                if self.active_session:
                    if len(self.site_offers_send) > 0:
                        history_docs = self.get_all_docs_from_mongo_collection(self.acc_history_collection,
                                                                               except_return_none=True)
                        if history_docs is not None:

                            time_threshold = int(time.time()) - 30

                            filtered_offers = [
                                offer for offer in self.site_offers_send
                                if offer['time'] > time_threshold
                            ]
                            unique_offers = {}

                            for offer in filtered_offers:
                                waxid = offer['id'] #
                                if waxid not in unique_offers:
                                    unique_offers[waxid] = offer
                                else:
                                    existing_offer_time = int(unique_offers[waxid]['time'])
                                    current_offer_time = int(offer['time'])
                                    if current_offer_time > existing_offer_time:
                                        unique_offers[waxid] = offer

                            self.cancel_steam_offer()
                            for key, value in unique_offers.items():
                                unique_site_id = key
                                site_item_id = key
                                trade_offer_url = value['tradelink']

                                steam_id = SteamClient.get_steam_id_from_url(trade_offer_url)
                                items_list = [item['assetid'] for item in value['json_tradeoffer']['me']['assets']]
                                successfully_send = self.send_steam_offer(history_docs, unique_site_id, trade_offer_url,
                                                                          steam_id, items_list)

                                offer_info = self.get_steam_offer_state(history_docs, unique_site_id)
                                offer_status = offer_info['offer status']
                                latest_offer = offer_info['latest offer']
                                if not successfully_send and offer_status and int(offer_status) not in [1, 4, 8, 10]:
                                    self.make_steam_offer(history_docs, unique_site_id, trade_offer_url, steam_id,
                                                          items_list, site_item_id=site_item_id)
                                self.confirm_steam_offer(offer_status, latest_offer, unique_site_id)
                        else:
                            raise ExitException
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Steam Send Offers Global Error: {e}", self.steamclient.username)
            time.sleep(self.steam_send_offers_global_time)

    def cancel_steam_offer(self):
        for offer in self.site_offers_cancel:
            trade_id = offer['tradeofferid']
            if trade_id not in self.site_offers_cancelled:
                response = self.steamclient.cancel_trade_offer(trade_id)
                if response:
                    self.site_offers_cancelled.append(trade_id)
                    Logs.log(f"Steam Send Offers: {trade_id} tradeID cancelled by Socket info",
                             self.steamclient.username)
                time.sleep(1)

    def confirm_steam_offer(self, offer_status, latest_offer, unique_site_id):
        trade_id = latest_offer['trade id']
        if offer_status:
            if int(offer_status) == 9:
                try:
                    headers = {"Authorization": f"Bearer {self.shadowpay_apikey}",
                               "trade_id": unique_site_id,
                               "tradeoffer_id": trade_id}
                    site_url = f'{self.site_url}/api/v2/user/trade'
                    response = requests.post(site_url, headers=headers, timeout=15).json()
                except:
                    response = None
                if response:
                    if 'success' in response and response['success']:
                        self.steamclient.confirm_trade_offer(trade_id)
                    else:
                        Logs.notify(self.tg_info, f"Steam Send Offers: Site didn't see {trade_id} tradeID:"
                                                  f" {response['msg']}", self.steamclient.username)
                        if self.steamclient.cancel_trade_offer(trade_id):
                            Logs.log(f"Steam Send Offers: {trade_id} tradeID cancelled", self.steamclient.username)
                        time.sleep(1)

                if int(time.time()) - latest_offer['time'] >= self.steam_detect_unconfirmed_offer_time:
                    Logs.notify(self.tg_info, f"Steam Send Offers: Unconfirmed {trade_id} tradeID",
                                self.steamclient.username)

    # endregion

    # region Site Socket
    def site_socket(self):  # Local Function by Steam Send Offers
        threading.Thread(target=self.receive_socket_events).start()
        while True:
            if self.ws.connected:
                if self.active_socket:
                    self.socket_ping()
                else:
                    self.socket_close()
            else:
                self.socket_connect()
            time.sleep(25)

    def socket_connect(self):
        if self.active_session:
            try:
                socket_info_url = f'{self.site_url}/api/v2/user/websocket'
                headers = {"Authorization": f"Bearer {self.shadowpay_apikey}"}
                socket_response = requests.get(socket_info_url, headers=headers, timeout=15).json()
                print(socket_response)
                if 'data' in socket_response and 'token' in socket_response['data'] and 'url' in socket_response['data']:
                    socket_token = socket_response['data']['token']
                    socket_url = socket_response['data']['url']
                    Logs.log(f"Socket connect", self.steamclient.username)
                    self.ws = websocket.WebSocket()
                    self.ws.connect(socket_url, timeout=60)
                    if self.ws.connected:
                        self.active_socket = False
                        auth = json.dumps({"id": 1, "params": {"token": socket_token}})
                        self.ws.send(auth)

                        Logs.log(f"Socket connected", self.steamclient.username)
            except:
                self.socket_close()

    def socket_ping(self):
        try:
            ping = json.dumps({"method": 7, "id": 1})
            self.ws.send(ping)
        except:
            self.socket_close()

    def socket_close(self):
        if self.ws.connected:
            try:
                self.ws.close()
                Logs.log(f"Socket closed", self.steamclient.username)
            except:
                pass

    def receive_socket_events(self):  # Local Function by Site Socket
        while True:
            try:
                if self.ws.connected:
                    message = self.ws.recv()
                    message = json.loads(message)
                    print(f'{message}')
                    if 'id' in message:
                        if 'result' in message:
                            self.active_socket = True
                            Logs.log(f"Socket authorized", self.steamclient.username)
                            if ('data' in message['result'] and 'data' in message['result']['data']
                                    and 'type' in message['result']['data']['data']
                                    and 'data' in message['result']['data']['data']):
                                message_type = message['result']['data']['data']['type']
                                message_data = message['result']['data']['data']['data']
                                if message_type == 'sendOffer':
                                    message_data['time'] = int(time.time())
                                    self.site_offers_send.append(message_data)
                                elif message_type in ['cancelOffer', 'declineOffer']:
                                    self.site_offers_cancel.append(message_data)
                else:
                    time.sleep(5)
            except:
                self.socket_close()
    # endregion
