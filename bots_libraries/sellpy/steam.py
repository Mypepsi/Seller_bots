from fake_useragent import UserAgent
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.mongo import Mongo
import io
import time
import pickle


class Steam(Mongo):
    def __init__(self):
        super().__init__()
        self.acc_history_collection = None
        self.ua = UserAgent()
        self.rate = 0
        self.commission = 0

    def take_session(self, steam_session):
        try:
            i = steam_session
            steam_cookie_file = io.BytesIO(i)
            self.steamclient = pickle.load(steam_cookie_file)
            self.steamclient.tm_api = self.content_acc_dict[self.steamclient.username]['tm apikey']
        except:
            Logs.notify_except(self.sellpy_tg_info, 'Error while taking Session', '')
            self.steamclient.username = Logs.get_ip_address()

    def steam_cancel_offers(self, acc_info, time_sleep, cancel_offers_sites_name):
        while True:
            try:
                self.update_account_data_info()
                current_time = time.time()
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                collection_name = f'history_{username}'
                self.acc_history_collection = self.get_collection(self.history, collection_name)

                active_trades = self.steamclient.get_trade_offers(self.steamclient.access_token, get_sent_offers=1,
                                                                  get_received_offers=0, get_descriptions=0, active_only=1,
                                                                  historical_only=0)
                if active_trades and 'response' in active_trades and 'trade_offers_sent' in active_trades['response']:
                    sites_name = []
                    for setting_offer in cancel_offers_sites_name:
                        if "site" in setting_offer:
                            sites_name.append(setting_offer["site"])
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
                            sent_time = record['sent time']
                        else:
                            site = "all"
                            sent_time = time_created

                        if site in sites_name:
                            validity_time = None
                            for item in cancel_offers_sites_name:
                                if item['site'] == site:
                                    validity_time = item['offers validity time']
                                    break
                            if validity_time is None:
                                continue
                            if current_time - sent_time > validity_time:
                                try:
                                    self.steamclient.cancel_trade_offer(tradeofferid)
                                    Logs.log(f'Steam Offer {tradeofferid} cancelled', self.steamclient.username)
                                except:
                                    pass
            except Exception as e:
                Logs.notify_except(self.sellpy_tg_info, f"Steam Cancel Offers Global Error: {e}",
                                   self.steamclient.username)

            time.sleep(time_sleep)

    def send_sold_item_info(self, site_name, hash_name, site_price, sold_price, acc_data_phases_inventory, currency,
                                  currency_symbol, document, tg_info):
        try:
            tg_id = tg_info['tg id']
            tg_bot = tg_info['tg bot']
            bot_name = tg_info['bot name']

            current_timestamp = int(time.time())

            middle_message = None
            service_max_price = None
            service_launch_price = None

            days = 0
            hours = 0
            minutes = 0

            profit = 0
            listed_time = 0
            launch_price = 0

            buff_full_price = 0
            steam_full_price = 0

            max_price = 0
            margin_max_price = 0

            max_limits_margin_max_price = 0
            min_limits_margin_max_price = 0

            for item in acc_data_phases_inventory.values():
                if hash_name == item["market_hash_name"]:
                    launch_price = item['launch_price']
                    service_launch_price = item['service_launch_price']
                    time_difference = current_timestamp - item['time']
                    days = time_difference // 86400
                    time_difference %= 86400
                    hours = time_difference // 3600
                    time_difference %= 3600
                    minutes = time_difference // 60
                    tm_seller_value = self.taking_information_for_price(site_name)
                    if tm_seller_value:
                        for condition in tm_seller_value:
                            phases_difference = time_difference / 86400
                            phases_key = str(self.find_matching_key(phases_difference, condition['days from']))
                            all_prices = self.content_database_prices['DataBasePrices']
                            for price in all_prices:
                                if hash_name in price and phases_key:
                                    try:
                                        max_price = float(price[hash_name]["max_price"])
                                        service_max_price = price[hash_name]['service_max_price']
                                        main_max_price = f'Max Price: {max_price}$ ({service_max_price}))\n'
                                        filtered_max_price = {key: value for key, value in price.items() if
                                                              key.endswith('_max_price') and (
                                                                          isinstance(value, float) or isinstance(value,
                                                                                                                 int))}
                                        different_max_prices = ''.join([f'{key}: {value}$\n' for key, value in filtered_max_price.items()])
                                        middle_message = main_max_price + different_max_prices + '\n'

                                        listed_time = item['time']
                                    except:
                                        Logs.log("Error during receiving Max Prices from DataBasePrices",
                                                 self.steamclient.username)

                                    try:
                                        price_range = self.find_matching_key(site_price,
                                                                             condition['days from'][
                                                                                 phases_key]['prices'])
                                        if price_range:
                                            margin_site_price = site_price * condition['days from'][phases_key]['prices'][price_range]
                                            max_limits_margin_max_price = round((margin_site_price * condition['days from'][phases_key][
                                                                                     'limits']['max']), 2)
                                            min_limits_margin_max_price = round((margin_site_price * condition['days from'][phases_key][
                                                                                     'limits']['min']), 2)
                                    except:
                                        Logs.log("Error during receiving min and max price limits",
                                                 self.steamclient.username)
                                    break
                            break
                    if max_price != 0:
                        profit = round((sold_price / max_price * 100 - 100), 2)
                    else:
                        profit = 0

            start_message = (
                f'{self.steamclient.username}\n'
                f'{bot_name}\n'
                f'{hash_name}\n'
                f'Site Price: {site_price}currency (Diapason: {min_limits_margin_max_price}{currency_symbol} '
                f'to {max_limits_margin_max_price}{currency_symbol})\n'
                f'Sold Price: {sold_price}$ (Sale Price: {margin_max_price}$)\n'
                f'Profit: {profit}%\n\n')
            end_message = (
                f'Buff Full price: {buff_full_price}$\n'
                f'Steam Full price: {steam_full_price}$\n'
                f'Launch Price: {launch_price}$)\n'
                f'Launch Price service: ({service_launch_price})\n'
            )
            if days == 0:
                sold_time_message = f'Sold Time {hours} hours: {minutes} min'
            elif hours == 0:
                sold_time_message = f'Sold Time {days} days: {minutes} min'
            elif days == 0 and hours == 0:
                sold_time_message = f'Sold Time {minutes} min'
            else:
                sold_time_message = f'Sold Time {days} days: {hours} hours: {minutes} min'

            if middle_message:
                message = start_message + middle_message + end_message + sold_time_message
            else:
                message = start_message + end_message + sold_time_message
            try:
                tg_bot.send_message(tg_id, message)
            except:
                pass

            info = {
                'site price': site_price,
                'currency': currency,
                'sold price': sold_price,
                'profit': (profit / 100 + 1),
                'max price': max_price,
                'max price service': service_max_price,
                'launch price': launch_price,
                'launch price service': service_launch_price,
                'listed time': listed_time
            }
            document.update(info)
            self.acc_history_collection.update_one({'_id': document['_id']}, {"$set": document})
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f"Send Sold Item Info Global Error: {e}", self.steamclient.username)














