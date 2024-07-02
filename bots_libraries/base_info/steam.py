from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.mongo import Mongo
from bots_libraries.steampy.client import SteamClient
from fake_useragent import UserAgent
import pickle
import io
import time
import threading
import requests


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

    def work_with_steam_settings(self, function, time_sleep):
        while True:
            self.update_account_data_info()
            for acc in self.content_acc_list:
                try:
                    username = acc['username']
                    session = self.content_acc_data_dict[username]['steam session']
                    self.take_session(session)
                    self.user_agent = self.steamclient.user_agent
                except:
                    self.user_agent = self.ua.random
                self.steamclient = SteamClient('', user_agent=self.user_agent)
                try:
                    self.steamclient.username = acc['username']
                    self.steamclient.password = acc['password']
                    self.steamclient.steam_id = acc['steam id']
                    self.steamclient.shared_secret = acc['shared secret']
                    self.steamclient.identity_secret = acc['identity secret']
                    self.steamclient.steam_guard = {"steamid": self.steamclient.steam_id,
                                        "shared_secret": self.steamclient.shared_secret,
                                        "identity_secret": self.steamclient.identity_secret
                                        }
                    self.steamclient.tm_api = self.get_key(acc, 'tm apikey')
                except Exception as e:
                    Logs.log(f'Error during taking information from account settings: {e}')

                proxy = acc['proxy']
                if proxy == "proxy":
                    self.steamclient.proxies = {"NoProxy": 1}
                else:
                    proxy_list = proxy.split(':')
                    proxy_ip = proxy_list[0]
                    proxy_port = proxy_list[1]
                    proxy_login = proxy_list[2]
                    proxy_password = proxy_list[3]

                    self.steamclient.proxies = {'http': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}',
                                  'https': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}'}

                    requests.proxies = self.steamclient.proxies

                function()
            modified_function_name = function.__name__.replace("_", " ").title()
            Logs.log(
                f'{modified_function_name}: All accounts authorized ({len(self.content_acc_list)} accounts in MongoDB)')
            time.sleep(time_sleep)

    def work_with_steam_data(self, function, time_sleep):
        while True:
            self.update_account_data_info()
            for acc in self.content_acc_data_list:
                steam_session = acc['steam session']
                self.take_session(steam_session)
                self.steamclient.username = acc['username']
                function()
            modified_function_name = function.__name__.replace("_", " ").title()
            Logs.log(f'{modified_function_name}: All accounts parsed ({len(self.content_acc_data_list)} accounts in MongoDB)')
            time.sleep(time_sleep)

    def work_with_steam_loop(self, function, time_sleep):
        while True:
            self.update_account_data_info()
            function()
            time.sleep(time_sleep)

    def work_with_steam_create_thread(self, function, function_time_sleep, thread_time_sleep):
        self.update_account_data_info()
        counter = 0
        for acc in self.content_acc_data_list:
            thread = threading.Thread(target=function, args=(acc, function_time_sleep))
            thread.start()
            counter += 1
            time.sleep(thread_time_sleep)
        modified_function_name = function.__name__.replace("_", " ").title()
        Logs.log(f'{modified_function_name}: {counter} threads are running '
                 f'({len(self.content_acc_data_list)} accounts in MongoDB)')

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
                active_trades = None
                pass
            active_trades = {
"response": {
"trade_offers_sent": [
{
"tradeofferid": "7061861937",
"accountid_other": 1726434001,
"message": "",
"expiration_time": 1718375554,
"trade_offer_state": 3,
"items_to_give": [
{
"appid": 730,
"contextid": "2",
"assetid": "37376417634",
"classid": "4149537607",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "2021"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417658",
"classid": "3608084516",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "452"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417672",
"classid": "4966324227",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "335"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417724",
"classid": "3955267134",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "78"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417734",
"classid": "720764395",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "24890"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417775",
"classid": "4726070138",
"instanceid": "1363818028",
"amount": "1",
"missing": True,
"est_usd": "266"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417799",
"classid": "3608084535",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "430"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417836",
"classid": "5931875063",
"instanceid": "5901378040",
"amount": "1",
"missing": True,
"est_usd": "493"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417892",
"classid": "311498445",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "18222"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417908",
"classid": "2735432289",
"instanceid": "1363818011",
"amount": "1",
"missing": True,
"est_usd": "218"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417931",
"classid": "310783170",
"instanceid": "1363818011",
"amount": "1",
"missing": True,
"est_usd": "184"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376417970",
"classid": "3608084872",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "455"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418020",
"classid": "937248672",
"instanceid": "1363818011",
"amount": "1",
"missing": True,
"est_usd": "261"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418042",
"classid": "937248672",
"instanceid": "1363818011",
"amount": "1",
"missing": True,
"est_usd": "261"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418072",
"classid": "310787063",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "61"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418099",
"classid": "4141779349",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "3870"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418113",
"classid": "4842645486",
"instanceid": "1363818011",
"amount": "1",
"missing": True,
"est_usd": "510"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418117",
"classid": "4578724347",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "3605"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418143",
"classid": "4722835233",
"instanceid": "1363818028",
"amount": "1",
"missing": True,
"est_usd": "311"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418169",
"classid": "4442051070",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "145"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418177",
"classid": "3560879471",
"instanceid": "1363818028",
"amount": "1",
"missing": True,
"est_usd": "841"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418183",
"classid": "3729328372",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "453"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418188",
"classid": "3608084982",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "549"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418198",
"classid": "3608083917",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "508"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418228",
"classid": "2735432289",
"instanceid": "1363818011",
"amount": "1",
"missing": True,
"est_usd": "218"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418271",
"classid": "310777578",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "1"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418279",
"classid": "3035570967",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "1"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418289",
"classid": "310777928",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "1"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418302",
"classid": "310776570",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "1"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418314",
"classid": "310776668",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "1"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418322",
"classid": "310776543",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "0"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418334",
"classid": "310776693",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "1"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418341",
"classid": "310777105",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "0"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418349",
"classid": "310776612",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "1"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376418374",
"classid": "469437901",
"instanceid": "1363818010",
"amount": "1",
"missing": True,
"est_usd": "1"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376450523",
"classid": "3955271324",
"instanceid": "1363818011",
"amount": "1",
"missing": True,
"est_usd": "45"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376493350",
"classid": "310776589",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "595"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376493364",
"classid": "5053951949",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "218"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376529488",
"classid": "5742258686",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "8097"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376529541",
"classid": "992089637",
"instanceid": "1363818008",
"amount": "1",
"missing": True,
"est_usd": "347"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376529594",
"classid": "4583009303",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "758"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376529602",
"classid": "4966071669",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "4249"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376529664",
"classid": "1440508502",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "342"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37376529672",
"classid": "2961159845",
"instanceid": "1363818028",
"amount": "1",
"missing": True,
"est_usd": "121"
},
{
"appid": 730,
"contextid": "2",
"assetid": "37453607056",
"classid": "4614850875",
"instanceid": "1363818004",
"amount": "1",
"missing": True,
"est_usd": "481"
}
],
"is_our_offer": True,
"time_created": 1717165954,
"time_updated": 1717166121,
"tradeid": "5359925671016975995",
"from_real_time_trade": False,
"escrow_end_date": 0,
"confirmation_method": 2,
"eresult": 1
}
],
"next_cursor": 0
}
}

            try:
                for offer in active_trades.get('response', {}).get('trade_offers_sent', []):
                    tradeofferid = offer['tradeofferid']
                    time_created = offer['time_created']

                    mongo_record = self.acc_history_collection.find({"trade id": tradeofferid}).sort("time", -1).limit(1)
                    record = next(mongo_record, None)

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
                        self.steamclient.cancel_trade_offer(self.steamclient.access_token, tradeofferid)

                time.sleep(time_sleep)

            except Exception as e:
                print(f"Error processing account {username}: {e}")
                time.sleep(time_sleep)











