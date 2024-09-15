import time
import requests
from bots_libraries.sellpy.logs import Logs
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
                        send_offers = self.get_all_docs_from_mongo_collection(self.acc_history_collection)

                        for i in range(len(request_site_offers)):
                            unique_site_id = request_site_offers[i]['tradeoffermessage']
                            partner = request_site_offers[i]['partner']
                            token = request_site_offers[i]['token']
                            items_list = [item['assetid'] for item in request_site_offers[i]['items']]
                            self.request_trade_ready(send_offers, unique_site_id)
                            successfully_send = self.send_steam_offer(request_site_offers[i],
                                                                      send_offers, unique_site_id)
                            if not successfully_send:
                                self.resend_steam_offer(request_site_offers[i], send_offers, unique_site_id)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Steam Send Offers Global Error: {e}", self.steamclient.username)
            time.sleep(self.steam_send_offers_global_time)

    def request_trade_ready(self, send_offers, unique_site_id):
        trade_ready_list = [offer for offer in send_offers if str(offer.get('site id')) == str(unique_site_id)]

        if len(trade_ready_list) > 0:
            latest_offer = max(trade_ready_list, key=lambda t: t['time'])
            trade_id = latest_offer['trade id']
            if trade_id is not None:
                try:
                    trade_ready_url = f'{self.site_url}/api/v2/trade-ready?key={self.tm_apikey}&tradeoffer={trade_id}'
                    requests.get(trade_ready_url, timeout=5)
                except:
                    pass
                time.sleep(1)

    # endregion
