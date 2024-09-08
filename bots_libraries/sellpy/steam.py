import io
import jwt
import time
import pickle
from bots_libraries.sellpy.mongo import Mongo
from bots_libraries.steampy.client import SteamClient
from bots_libraries.sellpy.logs import Logs, ExitException


class Steam(Mongo):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.active_session = False
        self.steamclient = SteamClient('')

        self.trade_url = None
        self.tm_apikey = None
        self.waxpeer_apikey = None
        self.csgoempire_apikey = None
        self.csgoempire_headers = None
        self.csgo500_user_id = self.csgo500_apikey = None
        self.jwt_api_key = None
        self.csgo500_jwt_apikey = None
        self.shadowpay_apikey = None
        self.buff_cookie = None

        self.steam_inventory_tradable = self.steam_inventory_full = self.steam_inventory_phases = {}

    # region Session
    def update_session(self, acc_info):  # Global Function (class_for_account_functions)
        while True:
            self.update_account_settings_info()
            self.update_account_data_info()
            self.active_session = self.take_session(acc_info)
            time.sleep(self.update_session_global_time)

    def take_session(self, acc_info):
        username = None
        try:
            if 'username' in acc_info:
                username = acc_info['username']
                if 'steam session' in acc_info:
                    session = acc_info['steam session']
                else:
                    if username in self.content_acc_data_dict and 'steam session' in self.content_acc_data_dict[username]:
                        session = self.content_acc_data_dict[username]['steam session']
                    else:
                        return False
                steam_cookie_file = io.BytesIO(session)
                self.steamclient = pickle.load(steam_cookie_file)
                self.acc_history_collection = self.get_collection(self.seller_history,
                                                                  f'history_{self.steamclient.username}')

                # Info from account_settings
                proxy = self.content_acc_settings_dict[self.steamclient.username]['proxy']
                if proxy == "proxy":
                    proxies = None
                else:
                    proxy_list = proxy.split(':')
                    proxy_ip = proxy_list[0]
                    proxy_port = proxy_list[1]
                    proxy_login = proxy_list[2]
                    proxy_password = proxy_list[3]
                    proxies = {'http': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}',
                               'https': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}'}
                self.steamclient.proxies = proxies
                self.steamclient.session.proxies.update(self.steamclient.proxies)
                self.trade_url = self.content_acc_settings_dict[self.steamclient.username]['trade url']
                self.tm_apikey = self.content_acc_settings_dict[self.steamclient.username]['tm apikey']
                self.waxpeer_apikey = self.content_acc_settings_dict[self.steamclient.username]['waxpeer apikey']
                self.csgoempire_apikey = self.content_acc_settings_dict[self.steamclient.username]['csgoempire apikey']
                self.csgoempire_headers = {
                    'Authorization': f'Bearer {self.csgoempire_apikey}'
                }
                self.csgo500_user_id = self.content_acc_settings_dict[self.steamclient.username]['csgo500 user id']
                self.csgo500_apikey = self.content_acc_settings_dict[self.steamclient.username]['csgo500 apikey']
                self.jwt_api_key = jwt.encode(
                    {'userId': self.csgo500_user_id},
                    self.csgo500_apikey,
                    algorithm="HS256"
                )
                self.csgo500_jwt_apikey = {'x-500-auth': self.jwt_api_key}
                self.shadowpay_apikey = self.content_acc_settings_dict[self.steamclient.username]['shadowpay apikey']
                raw_cookies = self.content_acc_settings_dict[self.steamclient.username]['buff cookie']
                if raw_cookies:
                    self.buff_cookie = dict(pair.split("=", 1) for pair in raw_cookies.split("; "))
                else:
                    self.buff_cookie = None

                # Info from account_data
                self.steamclient._api_key = self.content_acc_data_dict[self.steamclient.username]['steam apikey']
                self.steam_inventory_tradable = (
                                    self.content_acc_data_dict)[self.steamclient.username]['steam inventory tradable']
                self.steam_inventory_full = (
                                    self.content_acc_data_dict)[self.steamclient.username]['steam inventory full']
                self.steam_inventory_phases = (
                                    self.content_acc_data_dict)[self.steamclient.username]['steam inventory phases']

                return True
            else:
                raise ExitException
        except Exception as e:
            Logs.notify_except(self.tg_info, f'MongoDB: Error while taking Account Session: {e}', username)
            return False
    # endregion

    def steam_cancel_offers(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                self.update_account_data_info()
                if self.active_session:
                    current_time = int(time.time())
                    active_trades = self.steamclient.get_trade_offers(get_sent_offers=1, active_only=1)
                    if active_trades and 'response' in active_trades and 'trade_offers_sent' in active_trades['response']:
                        sites_name = []
                        for setting_offer in self.steam_cancel_offers_sites_name:
                            if "site" in setting_offer:
                                sites_name.append(setting_offer["site"])
                        for offer in active_trades['response']['trade_offers_sent']:
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
                                for item in self.steam_cancel_offers_sites_name:
                                    if item['site'] == site:
                                        validity_time = item['offer validity time']
                                        break
                                if validity_time is None:
                                    continue
                                if current_time - sent_time > validity_time:
                                    response = self.steamclient.cancel_trade_offer(tradeofferid)
                                    if response:
                                        Logs.log(f'Steam Cancel Offers: {tradeofferid} tradeID cancelled',
                                                 self.steamclient.username)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Steam Cancel Offers Global Error: {e}",
                                   self.steamclient.username)
            time.sleep(self.steam_cancel_offers_global_time)

    def check_created_steam_offer(self, creating_offer_time, assets_list, partner):
        trade_offers = self.steamclient.get_trade_offers(get_sent_offers=1)
        if trade_offers and 'response' in trade_offers and 'trade_offers_sent' in trade_offers['response']:
            trade_offers_sent = trade_offers['response']['trade_offers_sent']
            history_docs = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
            matched_trades = []
            for offer in trade_offers_sent:
                try:
                    time_created = offer['time_created']
                    match = False
                    for doc in history_docs:
                        if "trade id" in doc and doc["trade id"] == offer['tradeofferid']:
                            match = True
                            break
                    if match:
                        continue
                    if time_created > creating_offer_time - 15:
                        asset_id_from_trade_offers = [item['assetid'] for item in offer['items_to_give']]
                        if set(asset_id_from_trade_offers) == set(assets_list) and offer['accountid_other'] == partner:
                            matched_trades.append(offer)
                except:
                    pass
            if matched_trades:
                latest_trade_steam = max(matched_trades, key=lambda t: t['time_created'])
                if latest_trade_steam['trade_offer_state'] == 9:
                    try:
                        self.steamclient.confirm_trade_offer({'tradeofferid': latest_trade_steam['tradeofferid']})
                    except:
                        pass
                return latest_trade_steam['tradeofferid']
            else:
                return None
        else:
            return None

    def steam_history(self, collection_info):
        try:
            need_to_work = False
            for doc in collection_info:
                if 'steam status' in doc and doc['steam status'] in ['sent', 'again_sent', 'error_again_send']:
                    need_to_work = True
                    break

            if need_to_work:
                response = self.steamclient.get_trade_offers(get_sent_offers=1)

                if response and 'response' in response and 'trade_offers_sent' in response['response']:
                    trade_offers = response['response']['trade_offers_sent']
                    for doc in collection_info:
                        if ('steam status' in doc and doc['steam status'] in ['sent', 'again_sent', 'error_again_send']
                                and 'transaction' in doc and doc['transaction'] == 'sale_record'
                                and all(key in doc for key in ['site', 'trade id', 'asset id'])
                                and doc['site'] == self.site_name):
                            tradeofferid_alert = False

                            for offer in trade_offers:
                                if (all(key in offer for key in ['tradeofferid', 'items_to_give', 'trade_offer_state'])
                                        and offer['tradeofferid'] == doc['trade id']):
                                    tradeofferid_alert = True

                                    if not any(doc['asset id'] in item.values() for item in offer['items_to_give']):
                                        Logs.notify(self.tg_info, f"Steam History: MongoDB {doc['asset id']} assetID not"
                                                             f" in {offer['tradeofferid']} tradeID on steam history",
                                                    self.steamclient.username)

                                    current_timestamp = int(time.time())
                                    if offer['trade_offer_state'] in [2, 9]:
                                        break
                                    elif offer['trade_offer_state'] == 3:
                                        doc['steam status'] = 'accepted'
                                        doc['steam status time'] = current_timestamp
                                    elif offer['trade_offer_state'] == 6:
                                        doc['steam status'] = 'cancelled'
                                        doc['steam status time'] = current_timestamp
                                    elif offer['trade_offer_state'] == 7:
                                        doc['steam status'] = 'declined'
                                        doc['steam status time'] = current_timestamp
                                    else:
                                        doc['steam status'] = 'unavailable'
                                        doc['steam status time'] = current_timestamp
                                    try:
                                        self.acc_history_collection.update_one({'_id': doc['_id']}, {
                                            '$set': {'steam status': doc['steam status'], 'steam status time': doc[
                                                'steam status time']}})
                                    except:
                                        pass
                                    time.sleep(1)
                                    break

                            if not tradeofferid_alert:
                                Logs.notify(self.tg_info, f'Steam History: MongoDB {doc["trade id"]} tradeID not in steam history',
                                            self.steamclient.username)
        except Exception as e:
            Logs.notify_except(self.tg_info, f"Steam History Global Error: {e}", self.steamclient.username)
        time.sleep(3)

    def send_sold_item_info(self, hash_name, site_price, sold_price, currency, currency_symbol, document):
        try:
            current_timestamp = int(time.time())

            buff_full_price = 0
            steam_full_price = 0
            max_price = 0
            service_max_price = None
            middle_message = 'none price\n'

            launch_price = 0
            service_launch_price = None
            start_sale_time = 0
            sold_time_message = 'Sold Time:'
            max_price_with_margin = 0
            max_limits_site_price = 0
            min_limits_site_price = 0
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
                for item in self.steam_inventory_phases.values():
                    if str(document['asset id']) == item['asset_id']:
                        launch_price = item['launch_price']
                        service_launch_price = item['service_launch_price']
                        seller_value = self.get_information_for_price()
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
                f'{self.history_tg_info["bot name"]}\n'
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
                self.history_tg_info['tg bot'].send_message(self.history_tg_info['tg id'], message, timeout=5)
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
                Logs.notify_except(self.tg_info, f'Send Sold Item Info: MongoDB critical request failed: {e}',
                                   self.steamclient.username)
        except Exception as e:
            Logs.notify_except(self.tg_info, f"Send Sold Item Info Global Error: {e}", self.steamclient.username)
        time.sleep(3)
