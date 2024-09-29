import time
import json
import requests
import websocket
import threading
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.steampy.client import SteamClient


class WaxpeerSteam(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.site_offers_send = []
        self.site_offers_cancel = []
        self.ws = None
        # self.string = json.dumps({
        #     "name": "auth",
        #     "steamid": self.steamclient.steam_guard['steamid'],
        #     "apiKey": self.waxpeer_apikey,
        #     "tradeurl": self.trade_url
        # })

    # region Steam Send Offers
    def steam_send_offers(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url = f'{self.site_url}/api/v2/trade-request-give-p2p-all?key={self.tm_apikey}'
                        request_site = requests.get(url, timeout=15).json()
                        request_site_offers = request_site['offers']
                    except:
                        request_site_offers = None

                    if request_site_offers and isinstance(request_site_offers, list) and len(request_site_offers) > 0:
                        history_docs = self.get_all_docs_from_mongo_collection(self.acc_history_collection,
                                                                               except_return_none=True)
                        if history_docs is not None:
                            for i in range(len(request_site_offers)):
                                unique_site_id = request_site_offers[i]['tradeoffermessage']
                                partner = request_site_offers[i]['partner']
                                token = request_site_offers[i]['token']
                                trade_offer_url = f'https://steamcommunity.com/tradeoffer/new/?partner={partner}&token={token}'

                                steam_id = SteamClient.get_steam_id_from_url(trade_offer_url)
                                items_list = [item['assetid'] for item in request_site_offers[i]['items']]
                                successfully_send = self.send_steam_offer(history_docs, unique_site_id, trade_offer_url,
                                                                          steam_id, items_list)

                                offer_info = self.get_steam_offer_state(history_docs, unique_site_id)
                                offer_status = offer_info['offer status']
                                latest_offer = offer_info['latest offer']
                                if not successfully_send and offer_status and int(offer_status) not in [1, 4, 8, 10]:
                                    self.make_steam_offer(history_docs, unique_site_id, trade_offer_url, steam_id,
                                                          items_list)
                                self.confirm_steam_offer(offer_status, latest_offer)
                        else:
                            raise ExitException
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Steam Send Offers Global Error: {e}", self.steamclient.username)
            time.sleep(self.steam_send_offers_global_time)

    def confirm_steam_offer(self, offer_status, latest_offer):
        trade_id = latest_offer['trade id']
        if offer_status:
            if int(offer_status) == 9:
                self.steamclient.confirm_trade_offer(trade_id)
                if int(time.time()) - latest_offer['time'] >= self.steam_detect_unconfirmed_offer_time:
                    Logs.notify(self.tg_info, f"Steam Send Offers: "
                                              f"Unconfirmed {trade_id} tradeID",
                                self.steamclient.username)
        try:
            site_url = f'{self.site_url}/api/v2/trade-ready?key={self.tm_apikey}&tradeoffer={trade_id}'
            response = requests.get(site_url, timeout=15)
            if response['error'] in ["error InvalidResponseException", "error get info about trade",
                                     "error not active offers"]:
                Logs.notify(self.tg_info, f"Steam Send Offers: Site didn't see {trade_id} tradeID:"
                                          f" {response['error']}", self.steamclient.username)
                if self.steamclient.cancel_trade_offer(trade_id):
                    Logs.log(f'Steam Send Offers: {trade_id} tradeID cancelled', self.steamclient.username)
                time.sleep(1)
        except:
            pass

    # endregion

    # region Site Socket
    def site_socket(self):  # Local Function by Steam Send Offers
        self.socket_connect()

        send_ping_thread = threading.Thread(target=self.send_ping)
        send_auth_thread = threading.Thread(target=self.send_auth)
        receive_messages_thread = threading.Thread(target=self.receive_messages)

        send_ping_thread.start()
        send_auth_thread.start()
        receive_messages_thread.start()

        send_ping_thread.join()
        send_auth_thread.join()
        receive_messages_thread.join()

    def send_auth(self):
        while True:
            if self.ws:
                string = json.dumps({
                    "name": "auth",
                    "steamid": self.steamclient.steam_guard['steamid'],
                    "waxApi": self.waxpeer_apikey,
                    "tradeurl": self.trade_url
                })
                self.ws.send(string)
                print("Sent 'auth' to server")
                time.sleep(15)

    def send_ping(self):
        while True:
            if self.ws:
                online_send = json.dumps({"name": "ping"})
                self.ws.send(online_send)
                print("Sent 'ping' to server")
                time.sleep(10)

    def receive_messages(self):
        while True:
            try:
                message = self.ws.recv()
                message = json.loads(message)
                if 'name' in message and 'data' in message:
                    message_name = message['name']
                    message_data = message['data']
                    if message_name == 'pong':  # {'name': 'pong', 'data': {'msg': '1'}}
                        if 'msg' in message_data and message['data']['msg'] != '1':
                            Logs.notify(self.tg_info, f"Error during ping", self.steamclient.username)
                    if message == {'name': 'pong', 'data': {'msg': '1'}}:  #t
                        print(f'pong success')  #t

                    if message_name == 'user_change':  # {"name": "user_change", "data": {"can_p2p": True}}
                        if 'can_p2p' in message_data and not message_data['can_p2p']:
                            Logs.notify(self.tg_info, f"Error during auth", self.steamclient.username)
                    if message == {"name": "user_change", "data": {"can_p2p": True}}:  #t
                        print(f'user_change success')  #t

                    if message_name == 'send-trade':  # '{"name": "send-trade", "data": {"waxid": "d25s5f63-190s-46b4-8184-b9ec3d326932", "wax_id": "1234567", "json_tradeoffer": {"newversion": true, "version": 2, "me": {"assets": [{"appid": 730, "contextid": "2", "amount": 1, "assetid": "27509261111"}], "currency": [], "ready": false}, "them": {"assets": [{"appid": 730, "contextid": "2", "amount": 1, "assetid": "27509261111"}], "currency": [], "ready": false}}, "tradeoffermessage": "", "tradelink": "https://steamcommunity.com/tradeoffer/new/?partner=1234567890&token=asd1-5zF", "partner": "76561199059254XXX", "created": "2022-11-02T16:00:59.921Z", "now": "2022-11-02T16:01:16.311Z", "send_until": "2022-11-02T16:05:59.921Z"}}
                        if message_data not in self.site_offers_send:
                            self.site_offers_send.append(message_data)

                    if message_name == 'cancelTrade':  # {"name":"cancelTrade","data":{"trade_id":"5521581234","seller_steamid":"76561199059254XXX"}}
                        if message_data not in self.site_offers_cancel:
                            self.site_offers_cancel.append(message_data)
            except Exception as e:
                self.socket_restart()
                print(f"Error receiving message: {e}")

    def socket_connect(self):
        if not self.ws:
            self.ws = websocket.WebSocket()
            self.ws.connect('wss://wssex.waxpeer.com', timeout=25)

    def socket_close(self):
        if self.ws:
            print("WebSocket connection closed")

    def socket_restart(self):
        if self.ws:
            self.socket_close()
            time.sleep(5)
            self.socket_connect()

    # endregion
