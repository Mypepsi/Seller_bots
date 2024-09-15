import time
from bots_libraries.steampy.client import Asset
from bots_libraries.steampy.client import SteamClient
from bots_libraries.steampy.models import GameOptions
from bots_libraries.sellpy.session_manager import SessionManager
from bots_libraries.sellpy.logs import Logs


class SteamManager(SessionManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Steam Send Offers
    def send_steam_offer(self, response_data_offer, send_offers, unique_site_id):
        match = False
        for offer in send_offers:
            if 'site id' in offer and str(unique_site_id) == str(offer['site id']) and offer['trade id'] is not None:
                match = True
                break
        if not match:
            self.make_steam_offer(response_data_offer, send_offers)
            return True
        return False

    def resend_steam_offer(self, response_data_offer, send_offers, unique_site_id):
        for offer in send_offers:
            if 'site id' in offer and str(unique_site_id) == str(offer['site id']):
                trade_id = offer['trade id']
                if trade_id is None:
                    break

                response_state = self.steamclient.get_trade_offer_state(trade_id)
                time.sleep(1)

                if not isinstance(response_state, dict):
                    break

                if 'response' in response_state and 'offer' in response_state['response']:
                    offer_status = response_state['response']['offer']['trade_offer_state']
                else:
                    break

                if int(offer_status) == 9:
                    try:
                        self.steamclient.confirm_trade_offer({'tradeofferid': trade_id})
                    except:
                        pass
                    break

                if int(offer_status) not in [1, 4, 8, 10]:
                    break
                self.make_steam_offer(response_data_offer, send_offers)
                break

    def make_steam_offer(self, send_offers, unique_site_id, partner, token, assets_list):
        try:
            name_list = []
            assets_for_offer = []
            for asset_id in assets_list:
                my_asset = Asset(str(asset_id), GameOptions.CS)
                assets_for_offer.append(my_asset)

            trade_offer_url = f'https://steamcommunity.com/tradeoffer/new/?partner={partner}&token={token}'
            creating_offer_time = int(time.time())
            steam_response = self.steamclient.make_trade_offer(assets_for_offer, [], trade_offer_url)
            time.sleep(2)
            try:
                self.steamclient.confirm_trade_offer(steam_response)
            except:
                pass
            if steam_response is None or 'tradeofferid' not in steam_response:
                trade_offer_id = self.check_created_steam_offer(creating_offer_time, assets_list, partner)
                steam_response = {'tradeofferid': trade_offer_id}
            else:
                trade_offer_id = steam_response['tradeofferid']

            if trade_offer_id is not None:
                self.add_doc_in_history(send_offers, assets_list, name_list, unique_site_id, steam_response, trade_offer_url)
                Logs.log(f"Make Steam Offer: Trade sent: {name_list}", self.steamclient.username)
            else:
                self.add_doc_in_history(send_offers, assets_list, name_list, unique_site_id, steam_response, trade_offer_url,
                                           success=False)
                Logs.log(f"Make Steam Offer: Error send trade: {name_list}", self.steamclient.username)
        except Exception as e:
            Logs.notify_except(self.tg_info, f"Make Steam Offer Global Error: {e}", self.steamclient.username)

    def steam_cancel_offers(self):  # Global Function (class_for_account_functions)
        while True:
            try:
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

    def add_doc_in_history(self, send_offers, asset_list, name_list, unique_site_id, steam_response, trade_offer_url,
                           success=True):
        current_timestamp = int(time.time())
        current_timestamp_unique = int(time.time())
        if success:
            steam_status = 'sent'
            trade_id = steam_response['tradeofferid']
            sent_time = current_timestamp
        else:
            steam_status = 'error_send'
            trade_id = None
            sent_time = None

        doc_exist = False
        trade_id_in_mongo = None
        for entry in send_offers:
            if str(entry.get('site id')) == str(unique_site_id):
                trade_id_in_mongo = entry.get('trade id')
                doc_exist = True
                break

        for asset in asset_list:
            name = ''
            for item in self.steam_inventory_phases.values():
                if item['asset_id'] == asset:
                    name = item['market_hash_name']
                    name_list.append(name)
                    break
            if doc_exist:
                if success:
                    data = {
                        "steam status time": current_timestamp,
                        "trade id": trade_id
                    }
                    if trade_id_in_mongo is not None:
                        data['steam status'] = 'again_sent'
                    else:
                        data['steam status'] = steam_status
                        data['sent time'] = sent_time
                    try:
                        self.acc_history_collection.update_one(
                            {
                                "$and": [
                                    {"asset id": asset},
                                    {"site id": str(unique_site_id)}
                                ]
                            },
                            {
                                "$set": data
                            }
                        )
                    except Exception as e:
                        Logs.notify_except(self.tg_info, f"Steam Send Offers: MongoDB critical request failed: {e}",
                                           self.steamclient.username)
                else:
                    data = {
                        "steam status time": current_timestamp
                    }
                    if trade_id_in_mongo is not None:
                        data['steam status'] = 'error_again_send'
                        try:
                            self.acc_history_collection.update_one(
                                {
                                    "$and": [
                                        {"asset id": asset},
                                        {"site id": str(unique_site_id)}
                                    ]
                                },
                                {
                                    "$set": data
                                }
                            )
                        except Exception as e:
                            Logs.notify_except(self.tg_info, f"Steam Send Offers: MongoDB critical request failed: {e}",
                                               self.steamclient.username)
            else:
                current_timestamp_unique += 1
                steam_id = SteamClient.get_steam_id_from_url(trade_offer_url)
                data_append = {
                    "transaction": "sale_record",
                    "site": self.site_name,  # str
                    "time": current_timestamp_unique,  # int
                    "name": name,  # str
                    "steam status": steam_status,  # str
                    "steam status time": current_timestamp_unique,  # int
                    "site status": 'active_deal',
                    "site status time": current_timestamp_unique,  # int
                    "site id": str(unique_site_id),  # str
                    "buyer steam id": steam_id,  # i`m not sure)
                    "asset id": asset,  # str
                    "trade id": trade_id,  # str
                    "sent time": sent_time,  # int
                    "site item id": None
                }
                try:
                    self.acc_history_collection.insert_one(data_append)
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Steam Send Offers: MongoDB critical request failed: {e}",
                                       self.steamclient.username)


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
    # endregion

    # region History
    def steam_history(self, history_docs):
        try:
            need_to_work = False
            for doc in history_docs:
                if 'steam status' in doc and doc['steam status'] in ['sent', 'again_sent', 'error_again_send']:
                    need_to_work = True
                    break

            if need_to_work:
                response = self.steamclient.get_trade_offers(get_sent_offers=1)

                if response and 'response' in response and 'trade_offers_sent' in response['response']:
                    trade_offers = response['response']['trade_offers_sent']
                    for doc in history_docs:
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
                                        if (current_timestamp - int(offer['time_created'])) >= 86400:
                                            Logs.notify(self.tg_info, f"Steam History: "
                                                                      f"Active {offer['tradeofferid']} "
                                                                      f"tradeID more than 12 hours",
                                                        self.steamclient.username)
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
    # endregion
