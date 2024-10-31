import time
import requests
import calendar
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.steampy.client import Asset, SteamClient
from bots_libraries.steampy.models import GameOptions


class CSGO500Steam(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.dispute_id_list = []

    # region Steam Send Offers
    def steam_send_offers(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url = f'{self.site_url}/api/v1/market/listings/deposit/pending?appId=730&page=1'
                        request_site = requests.get(url, headers=self.csgo500_jwt_apikey, timeout=15).json()
                        request_site_offers = request_site['data']['listings']
                    except:
                        request_site_offers = None

                    if request_site_offers and isinstance(request_site_offers, list) and len(request_site_offers) > 0:
                        site_offers_send = site_offers_confirm = []
                        for offer in request_site_offers:
                            status_message = offer['shortStatus']
                            if status_message in ['market_waiting_tradeoffer', 'market_sent']:
                                site_offers_send.append(offer)
                            elif status_message == 'market_requested':
                                site_offers_confirm.append(offer)

                        self.confirm_site_deal(site_offers_confirm)

                        if len(site_offers_send) > 0:
                            history_docs = self.get_all_docs_from_mongo_collection(self.acc_history_collection,
                                                                                   except_return_none=True)
                            if history_docs is not None:
                                for i in range(len(request_site_offers)):
                                    site_item_id = unique_site_id = request_site_offers[i]['id']

                                    trade_offer_url = request_site_offers[i]['requestTradeURL']

                                    steam_id = SteamClient.get_steam_id_from_url(trade_offer_url)
                                    items_list = [item['assetId'] for item in request_site_offers[i]['item']]
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
            if offer['shortStatus'] == 'market_waiting_tradeoffer':
                date_string = offer['confirmDate']
                csgo500_time = time.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
                csgo500_time_unix = calendar.timegm(csgo500_time)
                current_time_unix = time.time()
                time_difference = current_time_unix - csgo500_time_unix
                if time_difference > self.steam_detect_unchanged_site_status_time:
                    Logs.notify(self.tg_info, f"Steam Send Offers: Unchanged site status in "
                                              f"{latest_offer['site id']} siteID", self.steamclient.username)
                try:
                    site_url = f'{self.site_url}/api/v1/market/listing/confirm-sent'
                    response = requests.get(site_url, data={"listingId": offer['id']}, timeout=15)
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

    def confirm_site_deal(self, site_offers_confirm):
        for offer in site_offers_confirm:
            try:
                site_url = f'{self.site_url}/api/v1/market/listing/confirm'
                requests.get(site_url, data={"listingId": offer['id']}, timeout=15)
            except:
                pass
            time.sleep(1)
    # endregion
