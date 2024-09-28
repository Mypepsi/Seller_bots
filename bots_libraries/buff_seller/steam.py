import time
import requests
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.steam_manager import SteamManager


class BuffSteam(SteamManager):

    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.sent_trades = []

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
                            name_list = []
                            trades_to_confirm = []
                            for trade in request_site_offers:
                                trade_offer_id = str(trade["tradeofferid"])
                                if trade_offer_id not in self.sent_trades:
                                    trades_to_confirm.append(trade_offer_id)
                            if len(trades_to_confirm) > 0:
                                for trade in trades_to_confirm:
                                    response = self.steamclient.accept_trade_offer(trade)
                                    if response:
                                        self.sent_trades.append(trade)
                                        self.add_doc_in_history()
                                        Logs.log(f"Make Steam Offer: Trade sent: {name_list}",
                                                 self.steamclient.username)
                                    else:
                                        self.add_doc_in_history(success=False)
                                        Logs.log(f"Make Steam Offer: Error send trade: "
                                                 f"{name_list}", self.steamclient.username)

                        else:
                            raise ExitException
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Steam Send Offers Global Error: {e}", self.steamclient.username)
            time.sleep(self.steam_send_offers_global_time)

    # endregion
