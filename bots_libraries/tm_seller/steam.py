import time
import requests
from bots_libraries.steampy.client import SteamClient
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.steam_manager import SteamManager


class TMSteam(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Steam Send Offers
    def steam_send_offers(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url = f'{self.site_url}/api/v2/trade-request-give-p2p-all?key={self.tm_apikey}'
                        request_site = requests.get(url, timeout=30).json()
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
            response = requests.get(site_url, timeout=30)
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
