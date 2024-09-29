import time
import requests
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.steam_manager import SteamManager


class BuffSteam(SteamManager):

    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Steam Send Offers
    def steam_send_offers(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url = f'{self.site_url}/api/market/steam_trade?_={int(time.time() * 1000)}'
                        request_site = requests.get(url, timeout=15).json()
                        request_site_offers = request_site["data"]
                    except:
                        request_site_offers = None

                    if request_site_offers and isinstance(request_site_offers, list) and len(request_site_offers) > 0:
                        history_docs = self.get_all_docs_from_mongo_collection(self.acc_history_collection,
                                                                               except_return_none=True)
                        if history_docs is not None:
                            for trade in request_site_offers:
                                if trade['state'] == 1:
                                    name_list = []
                                    tradeofferid = str(trade["tradeofferid"])
                                    unique_site_id = str(trade['id'])
                                    site_item_id = str(trade['id'])
                                    item_list = [item['assetid'] for item in trade['items_to_trade']]
                                    trade_offer = self.steamclient.get_trade_offer(tradeofferid)
                                    if (isinstance(trade_offer, dict) and 'response' in trade_offer
                                            and 'offer' in trade_offer['response']):
                                        offer_status = trade_offer['response']['offer']['trade_offer_state']
                                        steam_id = str(trade_offer['response']['offer']['accountid_other']
                                                       + 76561197960265728)
                                        if offer_status == 2:
                                            response = self.steamclient.accept_trade_offer(tradeofferid, steam_id)

                                            if response
                                                self.add_doc_in_history(history_docs, item_list, name_list, unique_site_id,
                                                                        tradeofferid, steam_id, site_item_id)
                                                Logs.log(f"Make Steam Offer: Trade sent: {name_list}",
                                                         self.steamclient.username)
                                            else:
                                                self.add_doc_in_history(history_docs, item_list, name_list, unique_site_id,
                                                                        tradeofferid, steam_id, site_item_id, success=False)
                                                Logs.log(f"Make Steam Offer: Error send trade: "
                                                         f"{name_list}", self.steamclient.username)

                        else:
                            raise ExitException
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Steam Send Offers Global Error: {e}", self.steamclient.username)
            time.sleep(self.steam_send_offers_global_time)

    # endregion
