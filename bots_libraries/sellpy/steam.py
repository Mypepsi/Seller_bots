import io
import time
import pickle
from bots_libraries.steampy.client import SteamClient
from bots_libraries.sellpy.mongo import Mongo
from bots_libraries.sellpy.logs import Logs, ExitException


class Steam(Mongo):
    def __init__(self, name):
        super().__init__(name)
        self.steamclient = SteamClient('')
        self.steamclient.username = None

    def take_session(self, acc, tg_info):
        username = None
        try:
            if 'username' in acc:
                username = acc['username']
                if 'steam session' in acc:
                    session = acc['steam session']
                else:
                    session = self.content_acc_data_dict[username]['steam session']
                steam_cookie_file = io.BytesIO(session)
                self.steamclient = pickle.load(steam_cookie_file)
                self.steamclient.username = acc['username']
                self.steamclient.tm_api = self.content_acc_settings_dict[self.steamclient.username]['tm apikey']
                return True
            else:
                raise ExitException
        except:
            Logs.notify_except(tg_info, 'MongoDB: Error while taking Account Session', username)
            self.steamclient.username = None
            return False

    def steam_cancel_offers(self, acc_info, global_time, tg_info, cancel_offers_sites_name):
        Logs.log('Steam Cancel Offers: thread are running', '')
        while True:
            try:
                current_time = int(time.time())
                self.update_account_data_info()
                active_session = self.take_session(acc_info, tg_info)
                if active_session:
                    collection_name = f'history_{self.steamclient.username}'
                    self.acc_history_collection = self.get_collection(self.history, collection_name)
                    if self.acc_history_collection:

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
                                        response = self.steamclient.cancel_trade_offer(tradeofferid)
                                        if response:
                                            Logs.log(f'Steam Cancel Offers: {tradeofferid} tradeID cancelled',
                                                     self.steamclient.username)
            except Exception as e:
                Logs.notify_except(tg_info, f"Steam Cancel Offers Global Error: {e}",
                                   self.steamclient.username)
            time.sleep(global_time)

    def send_sold_item_info(self, site_name, hash_name, site_price, sold_price, acc_data_phases_inventory, currency,
                                  currency_symbol, document, history_tg_info, tg_info):
        try:
            tg_id = history_tg_info['tg id']
            tg_bot = history_tg_info['tg bot']
            bot_name = history_tg_info['bot name']

            current_timestamp = int(time.time())

            buff_full_price = 0
            steam_full_price = 0
            max_price = 0
            service_max_price = None

            launch_price = 0
            service_launch_price = None
            start_sale_time = 0
            sold_time_message = 'Sold Time:'
            max_price_with_margin = 0
            max_limits_site_price = 0
            min_limits_site_price = 0
            middle_message = 'none price'
            profit = 0

            try:
                all_prices = self.content_database_prices['DataBasePrices']
                for price in all_prices:
                    if hash_name in price:
                        buff_full_price = price[hash_name]['buff_full_price']
                        steam_full_price = price[hash_name]['steam_full_price']
                        max_price = float(price[hash_name]["max_price"])
                        service_max_price = price[hash_name]['service_max_price']
                        filtered_max_price = {}
                        for item, prices in price.items():
                            filtered_max_price = {key: value for key, value in prices.items()
                                                  if key.endswith('_max_price') and (
                                                           isinstance(value, float) or isinstance(value, int))}
                        middle_message = ''.join(
                            [f'{key.replace("_max_", " ")}: {value}$\n' for key, value in filtered_max_price.items()])
                        break
            except:
                pass

            try:
                for item in acc_data_phases_inventory.values():
                    if str(document['asset id']) == item['asset_id']:
                        launch_price = item['launch_price']
                        service_launch_price = item['service_launch_price']
                        seller_value = self.get_information_for_price(tg_info, site_name)
                        start_sale_time = item['time']

                        time_difference = time_difference_ = current_timestamp - item['time']
                        days = time_difference_ // 86400
                        time_difference_ %= 86400
                        hours = time_difference_ // 3600
                        time_difference_ %= 3600
                        minutes = time_difference_ // 60
                        if days > 0:
                            sold_time_message += f' {days} days'
                        if hours > 0:
                            sold_time_message += f' {hours} hours'
                        if minutes > 0:
                            sold_time_message += f' {minutes} min'

                        if seller_value:
                            for condition in seller_value:
                                if condition['date to'] >= start_sale_time >= condition['date from']:
                                    phases_difference = time_difference / 86400
                                    phases_key = self.find_matching_key(phases_difference, condition['days from'])
                                    if phases_key:
                                        price_range = self.find_matching_key(max_price, condition['days from'][
                                                                                 phases_key]['prices'])
                                        if price_range:
                                            max_price_with_margin = round(max_price * condition['days from'][phases_key]['prices'][
                                                price_range], 3)
                                            site_price_with_margin = site_price * condition['days from'][phases_key]['prices'][price_range]
                                            max_limits_site_price = round((site_price_with_margin * condition['days from'][phases_key][
                                                                                     'limits']['max']), 2)
                                            min_limits_site_price = round((site_price_with_margin * condition['days from'][phases_key][
                                                                                     'limits']['min']), 2)
                                        break
                        if max_price != 0:
                            profit = round((sold_price / max_price * 100 - 100), 2)
            except:
                pass

            message = (
                f'{bot_name}\n'
                f'{self.steamclient.username}\n'
                f'{hash_name}\n'
                f'Site Price: {site_price}{currency_symbol} (Diapason: {min_limits_site_price}{currency_symbol} '
                f'to {max_limits_site_price}{currency_symbol})\n'
                f'Sold Price: {sold_price}$ (Sale Price: {max_price_with_margin}$)\n'
                f'Profit: {profit}%\n\n'
                f'Max Price: {max_price}$ ({service_max_price})\n'
                f'{middle_message}\n'
                f'Buff Full price: {buff_full_price}$\n'
                f'Steam Full price: {steam_full_price}$\n'
                f'Launch Price: {launch_price}$ ({service_launch_price})\n'
                f'{sold_time_message}'
            )

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
                'listed time': start_sale_time
            }
            document.update(info)

            try:
                self.acc_history_collection.update_one({'_id': document['_id']}, {"$set": document})
            except Exception as e:
                Logs.notify_except(tg_info, f'Send Sold Item Info: MongoDB critical request failed: {e}',
                                   self.steamclient.username)
        except Exception as e:
            Logs.notify_except(tg_info, f"Send Sold Item Info Global Error: {e}", self.steamclient.username)
        time.sleep(3)