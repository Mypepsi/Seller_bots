import time
import json
import requests
import calendar
import websocket
import threading
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.steampy.client import SteamClient



class CSGOEmpireSteam(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.dispute_id_list = []

        self.site_offers_send = []
        self.site_offers_cancel = []
        self.site_offers_cancelled = []
        self.ws = websocket.WebSocket()
        self.active_socket = False

    # region Steam Send Offers
    def steam_send_offers(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url = f'{self.site_url}/api/v2/trading/user/trades'
                        request_site = requests.get(url, headers=self.csgoempire_headers, timeout=15).json()
                        request_site_offers = request_site['data']['deposits']
                    except:
                        request_site_offers = None

                    if request_site_offers and isinstance(request_site_offers, list) and len(request_site_offers) > 0:
                        site_offers_send = site_offers_dispute = []
                        for offer in request_site_offers:
                            status_message = offer['status_message']
                            if status_message in ['Sending', 'Sent']:
                                site_offers_send.append(offer)
                            elif status_message == 'Disputed':
                                site_offers_dispute.append(offer)

                        for offer in site_offers_dispute:
                            if offer['id'] not in self.dispute_id_list:
                                Logs.notify(self.tg_info, f"Active Dispute: \n{offer['item']['market_name']}\n"
                                                          f"Site Price: {offer['item']['market_value']} coins\n"
                                                          f"ID: {offer['id']}", self.steamclient.username)
                                self.dispute_id_list.append(offer['id'])

                        if len(site_offers_send) > 0:
                            history_docs = self.get_all_docs_from_mongo_collection(self.acc_history_collection,
                                                                                   except_return_none=True)
                            if history_docs is not None:
                                for i in range(len(request_site_offers)):
                                    unique_site_id = request_site_offers[i]['id']
                                    site_item_id = request_site_offers[i]['item_id']
                                    trade_offer_url = request_site_offers[i]['metadata']['trade_url']

                                    steam_id = SteamClient.get_steam_id_from_url(trade_offer_url)
                                    items_list = [item['asset_id'] for item in request_site_offers[i]['item']]
                                    successfully_send = self.send_steam_offer(history_docs, unique_site_id,
                                                                              trade_offer_url, steam_id, items_list)

                                    offer_info = self.get_steam_offer_state(history_docs, unique_site_id)
                                    offer_status = offer_info['offer status']
                                    latest_offer = offer_info['latest offer']
                                    if not successfully_send and offer_status and int(offer_status) not in [1, 4, 8, 10]:
                                        self.make_steam_offer(history_docs, unique_site_id, trade_offer_url, steam_id,
                                                              items_list, site_item_id=site_item_id)
                                    self.confirm_steam_offer(offer_status, latest_offer, request_site_offers[i])
                            else:
                                raise ExitException
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Steam Send Offers Global Error: {e}", self.steamclient.username)
            time.sleep(self.steam_send_offers_global_time)

    def confirm_steam_offer(self, offer_status, latest_offer, offer):
        trade_id = latest_offer['trade id']
        if offer_status is not None:
            if offer['status_message'] == 'Sending':
                date_string = offer['updated_at']
                empire_time = time.strptime(date_string, "%Y-%m-%d %H:%M:%S")
                empire_time_unix = calendar.timegm(empire_time)
                current_time_unix = time.time()
                time_difference = current_time_unix - empire_time_unix
                if time_difference > self.steam_detect_unchanged_site_status_time:
                    Logs.notify(self.tg_info, f"Steam Send Offers: Unchanged site status in "
                                              f"{latest_offer['site id']} siteID", self.steamclient.username)
                try:
                    site_url = f'{self.site_url}/api/v2/trading/deposit/{trade_id}/sent'
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
            if int(offer_status) == 9:
                self.steamclient.confirm_trade_offer(trade_id)
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
            time.sleep(10)

    def socket_connect(self):
        if self.active_session:
            try:
                socket_info_url = f'{self.site_url}/api/v2/metadata/socket'
                headers = {"Authorization": f"Bearer {self.csgoempire_apikey}"}
                socket_response = requests.get(socket_info_url, headers=headers, timeout=15).json()
                Logs.log(f"Socket connect", self.steamclient.username)
                self.ws = websocket.WebSocket()
                self.ws.connect(f'wss://trade.csgoempire.io/s/?EIO=3&transport=websocket', timeout=60)
                if self.ws.connected:
                    self.active_socket = False
                    ping = f'40/trade,'
                    self.ws.send(ping)
                    if ('user' in socket_response and 'id' in socket_response['user']
                            and 'socket_token' in socket_response and 'socket_signature' in socket_response and
                            'last_session' in socket_response['user'] and
                            'device_identifier' in socket_response['user']['last_session']):
                        auth = {
                            "uid": socket_response['user']['id'],
                            "model": socket_response['user'],
                            "authorizationToken": socket_response['socket_token'],
                            "signature": socket_response['socket_signature'],
                            "uuid": 'null'
                        }
                        string_to_send_2 = f'42/trade,["identify",{json.dumps(auth, separators=(",", ":"))}]'.replace(
                            '\'', '"').replace('True', 'true').replace('False', 'false').replace('None', 'null')
                        self.ws.send(string_to_send_2)
                        Logs.log(f"Socket connected", self.steamclient.username)
                    else:
                        Logs.log(f"Socket NO connected", self.steamclient.username)
            except:
                self.socket_close()

    def socket_ping(self):
        try:
            ping = '2'
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
                    if '{"authenticated":true' in message:
                        self.active_socket = True
            except:
                self.socket_close()
    # endregion
