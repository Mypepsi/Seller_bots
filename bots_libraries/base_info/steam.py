from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.mongo import Mongo
from fake_useragent import UserAgent
import pickle
import io
import time


class Steam(Mongo):
    def __init__(self):
        super().__init__()
        self.acc_history_collection = None
        self.questionable_proxies = {}
        self.ua = UserAgent()

    def take_session(self, steam_session):
        i = steam_session
        steam_cookie_file = io.BytesIO(i)
        self.steamclient = pickle.load(steam_cookie_file)
        self.steamclient.tm_api = self.content_acc_dict[self.steamclient.username]['tm apikey']

    def check_trades_for_cancel(self, acc_info, cancel_offers_sites_name, time_sleep):
        while True:
            self.update_account_data_info()
            current_time = time.time()
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
            except:
                username = ''
                Logs.log('Error during taking a session')
            collection_name = f'history_{username}'
            try:
                self.acc_history_collection = self.get_collection(self.history, collection_name)
            except:
                Logs.log(f'Collecrion {collection_name} does not exist')

            try:
                active_trades = self.steamclient.get_trade_offers(self.steamclient.access_token, get_sent_offers=1,
                                                         get_received_offers=0, get_descriptions=0, active_only=1,
                                                         historical_only=0)
            except:
                Logs.log(f'{username}: Steam active offers loading Error')
                active_trades = None


            if active_trades and 'response' in active_trades and 'trade_offers_sent' in active_trades['response']:
                try:
                    for offer in active_trades.get('response', {}).get('trade_offers_sent', []):
                        tradeofferid = offer['tradeofferid']
                        time_created = offer['time_created']

                        try:
                            mongo_record = (self.acc_history_collection.find
                                            ({"trade id": tradeofferid}).sort("time", -1).limit(1))
                            record = next(mongo_record)
                        except:
                            record = None

                        if record:
                            site = record['site']
                            time_sent = record['time']
                        else:
                            site = "all"
                            time_sent = time_created

                        cancel_time = None
                        for item in cancel_offers_sites_name:
                            if item['site'] == site:
                                cancel_time = item['cancel_offers_time']
                                break

                        if cancel_time is None and site != "all":
                            continue

                        if current_time - time_sent > cancel_time:
                            self.steamclient.cancel_trade_offer(tradeofferid)
                            Logs.log(f'{username}: {tradeofferid} Steam Offer cancelled')
                except Exception as e:
                    Logs.log(f"Error processing account {username}: {e}")
                time.sleep(time_sleep)











