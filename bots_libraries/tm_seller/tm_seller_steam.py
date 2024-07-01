from bots_libraries.base_info.logs import Logs
from bots_libraries.creator.creator_steam import Steam
from bots_libraries.steampy.models import GameOptions
from bots_libraries.steampy.client import Asset
import time
import requests


class TMSteam(Steam):
    def __init__(self):
        super().__init__()
        self.acc_history_collection = None
        self.commission = 0
        self.rate = 0

    #region tm sda
    def request_give_p2p_all(self, username):
        try:
            url = f'https://market.csgo.com/api/v2/trade-request-give-p2p-all?key={self.steamclient.tm_api}'
            response = requests.get(url, timeout=10)
            response_data = response.json()
            return response_data
        except Exception:
            return None

    def make_steam_offer(self, response_data_offer, send_offers, inventory_phases):
        try:
            names = []
            assets = []
            assets_for_offer = []
            msg = response_data_offer['tradeoffermessage']
            for as_ in response_data_offer['items']:
                asset_id = as_['assetid']
                assets.append(asset_id)
                my_asset = Asset(str(asset_id), GameOptions.CS)
                assets_for_offer.append(my_asset)

            partner = response_data_offer['partner']
            token = response_data_offer['token']
            trade_offer_url = f'https://steamcommunity.com/tradeoffer/new/?partner={partner}&token={token}'
            try:
                steam_response = self.steamclient.make_offer_with_url(assets_for_offer, [], trade_offer_url, '')
                confirm_steam_response = self.steamclient.confirm_offer_via_tradeofferid(steam_response)
                time.sleep(3)
                if 'tradeofferid' in confirm_steam_response:
                    self.handle_tm_history_doc(inventory_phases, send_offers, assets, names, msg, confirm_steam_response)
                    Logs.log(f"{self.steamclient.username}: Steam Trade Sent: {names}")
                else:
                    Logs.log(f"{self.steamclient.username}: Steam Trade Error : {names}")
            except Exception as e:
                self.handle_tm_history_doc(inventory_phases, send_offers, assets, names, msg, None,
                                           success=False)
                self.check_created_trade(assets_for_offer, partner)
                Logs.log(f'Error when sending a steam trade: {e}')
        except Exception as e:
            Logs.log(f'Critical error during make steam offer: {e}')

    def check_created_trade(self, assets, partner):
        trade_offers = self.steamclient.get_trade_offers(self.steamclient.access_token, get_sent_offers=1,
                                                         get_received_offers=0, get_descriptions=0, active_only=0,
                                                         historical_only=0)
        if trade_offers and 'response' in trade_offers and 'trade_offers_sent' in trade_offers['response']:
            current_time = int(time.time())
            trade_offers_sent = trade_offers['response']['trade_offers_sent']

            matched_trades = []
            for offer in trade_offers_sent:
                time_created = offer['time_created']
                if time_created > current_time - 5:
                    if set(offer['items_to_give']) == set(assets) and offer['accountid_other'] == partner:
                        if not self.is_trade_in_mongo(offer['tradeofferid']): #і сайт тм
                            matched_trades.append(offer)

            if matched_trades:
                latest_trade = max(matched_trades, key=lambda t: t['time_created'])  #шукає останій трейд в latest_trade
                if latest_trade['trade_offer_state'] == 9:
                    self.steamclient.confirm_offer_via_tradeofferid({'tradeofferid': latest_trade['tradeofferid']})

    def is_trade_in_mongo(self, tradeofferid) -> bool:
        return self.acc_history_collection.find_one({"trade id": tradeofferid}) is not None

    def handle_tm_history_doc(self, inventory_phases, send_offers, assets_list, name_list, msg, steam_response,
                              success=True):
        current_timestamp = int(time.time())
        if success:
            steam_status = 'sent'
            trade_id = steam_response['tradeofferid']
            sent_time = current_timestamp
        else:
            steam_status = 'error_send'
            trade_id = None
            sent_time = None

        for asset in assets_list:
            name = ''
            for item in inventory_phases.values():
                if item['asset_id'] == asset:
                    name = item['market_hash_name']
                    name_list.append(name)
                    break
            name_exists = any(entry.get('site id') == msg for entry in send_offers)

            if name_exists:
                if success:
                    steam_status = 'again_sent'
                    self.acc_history_collection.update_one(
                        {
                            "$and": [
                                {"asset id": asset},
                                {"site id": msg}
                            ]
                        },
                        {
                            "$set": {
                                "steam status": steam_status,
                                "status time": current_timestamp,
                                "sent time": sent_time,
                                "trade id": trade_id
                            }
                        }
                    )
                else:
                    steam_status = 'error_again_sent'
                    self.acc_history_collection.update_one(
                        {
                            "$and": [
                                {"asset id": asset},
                                {"site id": msg}
                            ]
                        },
                        {
                            "$set": {
                                "steam status": steam_status
                            }
                        }
                    )
            else:
                data_append = {
                    "transaction": "sale_record",
                    "site": "tm",
                    "time": current_timestamp,
                    "name": name,
                    "steam status": steam_status,
                    "site status": 'active_deal',
                    "status time": current_timestamp,
                    "site id": msg,
                    "asset id": asset,
                    "trade id": trade_id,
                    "sent time": sent_time
                }
                self.acc_history_collection.insert_one(data_append)

    def tm_trades(self, acc_info, time_sleep):
        while True:
            self.update_account_data_info()
            username = ''
            acc_data_inventory_phases = []
            try:
                username = acc_info['username']
                acc_data_inventory_phases = acc_info['steam inventory phases']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
            except:
                Logs.log('Error during taking a session')
            collection_name = f'history_{username}'
            try:
                self.acc_history_collection = self.get_collection(self.history, collection_name)
            except:
                Logs.log(f'Collecrion {collection_name} does not exist')
            response_data = self.request_give_p2p_all(username)
            if response_data is not None and 'offers' in response_data and type(response_data['offers']) == list:
                send_offers = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
                for i in range(len(response_data['offers'])):
                    try:
                        msg = response_data['offers'][i]['tradeoffermessage']
                        unique_msg_in_send_offers = []
                        for offer in send_offers:  # Trade ready:
                            try:
                                trade_id = offer['trade_id']
                                data_text = offer['text']
                                if msg == data_text:
                                    trade_ready_url = (f'https://market.csgo.com/api/v2/trade-ready?'
                                           f'key={self.steamclient.tm_api}&tradeoffer={trade_id}')
                                    requests.get(trade_ready_url, timeout=10)
                            except:
                                pass

                        for offer in send_offers:  # Resending
                            if msg in offer.values() and msg not in unique_msg_in_send_offers:
                                unique_msg_in_send_offers.append(msg)
                                trade_id = offer['trade id']
                                if trade_id is None:
                                    continue

                                response_steam_trade_offer = self.steamclient.get_trade_offer_state(trade_id)

                                if not isinstance(response_steam_trade_offer, dict):
                                    continue

                                if 'response' in response_steam_trade_offer and 'offer' in response_steam_trade_offer['response']:
                                    offer_status = response_steam_trade_offer['response']['offer']['trade_offer_state']
                                else:
                                    continue

                                if int(offer_status) == 9:
                                    self.steamclient.confirm_offer_via_tradeofferid({'tradeofferid': trade_id})
                                    continue

                                if int(offer_status) not in [1, 4, 8, 10]:
                                    continue

                            self.make_steam_offer(response_data['offers'][i], send_offers, acc_data_inventory_phases)
                    except:
                        Logs.log('Error in tm trades')
            elif 'error' in response_data:
                if response_data['error'] == 'nothing':
                    Logs.log('There is no need to transfer anything')
            time.sleep(time_sleep)

    #endregion


    #region add to sale
    def get_and_filtered_inventory(self, inventory_from_acc_data):
        try:
            update_inventory_url = f'https://market.csgo.com/api/v2/update-inventory/?key={self.steamclient.tm_api}'
            requests.get(update_inventory_url, timeout=10)
            time.sleep(3)
            my_inventory_url = f'https://market.csgo.com/api/v2/my-inventory/?key={self.steamclient.tm_api}'
            my_inventory = requests.get(my_inventory_url, timeout=10)
            my_inventory = my_inventory.json()
            my_inventory_list = []
            if my_inventory['success']:
                try:
                    my_inventory_items = my_inventory['items']
                    my_inventory_list = [item['id'] for item in my_inventory_items]
                except Exception:
                    pass
            else:
                Logs.log('Error during receiving inventory')

            acc_data_inventory_assets_id = [item['asset_id'] for item in inventory_from_acc_data.values()]
            filtered_inventory = [item for item in my_inventory_list if item in acc_data_inventory_assets_id]
            return filtered_inventory
        except:
            return None

    @staticmethod
    def find_matching_key(wanted, dictionary):
        keys = sorted([int(k) for k in dictionary.keys()])  # turn into integer
        found_key = None
        for i in range(len(keys) - 1):
            if keys[i] <= wanted < keys[i + 1]:
                found_key = str(keys[i])
                break
        if found_key is None and wanted >= keys[-1]:
            found_key = str(keys[-1])
        return found_key

    def get_my_market_price(self, asset_id_in_phases_inventory, conditions):
        start_sale_time = asset_id_in_phases_inventory['time']
        hash_name = asset_id_in_phases_inventory['market_hash_name']
        for condition in conditions:
            if condition['date to'] >= start_sale_time >= condition['date from']:
                current_timestamp = int(time.time())
                phases_difference = (current_timestamp - start_sale_time) // 86400
                phases_key = self.find_matching_key(phases_difference, condition['days from'])
                all_prices = self.content_database_prices['DataBasePrices']
                for price in all_prices:
                    if hash_name in price:
                        max_price = float(price[hash_name]["max_price"])
                        price_range = self.find_matching_key(max_price,
                                                             condition['days from'][phases_key]['prices'])
                        margin_max_price = max_price * condition['days from'][phases_key]['prices'][price_range]
                        limits_margin_max_price = (margin_max_price *
                                                   condition['days from'][phases_key]['limits']['max'])

                        try:
                            market_price = round(limits_margin_max_price * self.commission * self.rate, 2)
                        except:
                            market_price = 0
                        return market_price
        return None

    def add_to_sale(self, acc_info, time_sleep):
        while True:
            self.update_account_data_info()
            self.update_db_prices_and_setting()
            acc_data_tradable_inventory = {}
            acc_data_phases_inventory = {}
            try:
                acc_data_tradable_inventory = acc_info['steam inventory tradable']
                acc_data_phases_inventory = acc_info['steam inventory phases']

                steam_session = acc_info['steam session']
                self.take_session(steam_session)
            except:
                Logs.log('Error during taking a session')
            filtered_inventory = self.get_and_filtered_inventory(acc_data_tradable_inventory)

            try:
                self.commission = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_commission']
                self.rate = self.content_database_settings['DataBaseSettings']['TM_Seller']['TM_Seller_rate']
            except:
                Logs.log(f'Error during taking a info from DataBaseSettings -> TM_Seller')
            try:
                database_setting_bots = self.content_database_settings['DataBaseSettings']['Sellers_SalePrice']['bots']
            except:
                database_setting_bots = {}
                Logs.log(f'Error during taking a info from DataBaseSettings -> Sellers_SalePrice -> bots')

            tm_seller_value = None
            for key, value in database_setting_bots.items():
                if 'tm_seller' in key:
                    tm_seller_value = value
                    break
            for asset_id in filtered_inventory:
                market_price = self.get_my_market_price(acc_data_phases_inventory[asset_id], tm_seller_value)
                add_to_sale_url = (f'https://market.csgo.com/api/v2/add-to-sale?key={self.steamclient.tm_api}'
                       f'&cur=RUB&id={asset_id}&price={market_price}')
                #requests.get(add_to_sale_url, timeout=10)
                time.sleep(2)
            time.sleep(time_sleep)
    #endregion


    def check_trades_for_cancel(self):
        tm_timer = Settings.return_setting(Bot.general_settings_path, 'cancel_active_send_offers_tm', 'int')
        while True:
            if number_of_try > 2:
                now = datetime.now()
                self.logs.write_log(SDA.log_path,
                                    f'check_active_send_offers: Не загружен список активных офферов (лагает стим апи).')

                return False
            try:
                response = self.steam_client.get_trade_offers()
                now = datetime.now()
                self.logs.write_log(SDA.log_path,
                                    f'check_active_send_offers: Загружен список активных офферов.')

                break
            except Exception:
                number_of_try += 1
                continue

        time_to_cancel_normal = Settings.return_setting(Bot.general_settings_path, Bot.cancel_active_send_offers, 'int')
        # обработка ответа от апи стима
        if not ('response' in response and 'trade_offers_sent' in response['response']):
            return

        # чтение файла с трейдами от ксго500, tm, empire
        sent_offers = Bot.file_with_lock('data/sda/cancel_active_send_offers.txt', 'r').split('\n')
        offers_sent = {}
        for offer in sent_offers:
            try:
                data = json.loads(offer)
                offers_sent.update({data['trade_id']: {'platform': data['platform'], 'asset_id':  data['asset_id'], "text": data["text"]}})
                if data['platform'] != 'polygon':
                    offers_sent[data['trade_id']].update({'sent_time':  data['sent_time']})
            except:
                continue

        # поиск минимального времени отмены для каждого трейда
        for offer in offers_sent:
            asset_id = offers_sent[offer]['asset_id']
            platform = offers_sent[offer]['platform']
            uniq_text = offers_sent[offer]['text']
            if platform == 'polygon':
                continue

            for offer_ in sent_offers:
                try:
                    data = json.loads(offer_)
                    asset_id_ = data['asset_id']
                    platform_ = data['platform']
                    uniq_text_ = data['text']
                    if asset_id_ == asset_id and platform_ == platform and uniq_text == uniq_text_:
                        offers_sent[offer]['sent_time'] = data['sent_time']
                        break
                except:
                    continue

        trades_to_cancel = []
        for trade in response['response']['trade_offers_sent']:
            trade_id = trade['tradeofferid']
            if trade_id in offers_sent:
                service = offers_sent[trade_id]['platform']
                if service == 'empire':
                    time_to_cancel = empire_timer
                elif service == 'tm':
                    time_to_cancel = tm_timer
                elif service == 'csgo500':
                    time_to_cancel = csgo500_timer
                elif service == 'polygon':
                    time_to_cancel = polygon_timer
                elif service == 'waxpeer':
                    time_to_cancel = waxpeer_timer
                else:
                    time_to_cancel = time_to_cancel_normal

                if service == 'polygon':
                    time_updated = trade['time_updated']
                else:
                    time_updated = offers_sent[trade_id]['sent_time']

            else:
                time_to_cancel = time_to_cancel_normal
                time_updated = trade['time_updated']

            if time_updated + time_to_cancel <= int(time.time()):
                trades_to_cancel.append(trade['tradeofferid'])

        for trade in trades_to_cancel:

            number_of_try = 0
            while True:
                if number_of_try > 2:
                    return False
                try:
                    response_s = self.steam_client.cancel_trade_offer(trade)
                    if 'tradeofferid' in response_s:
                        now = datetime.now()
                        self.logs.write_log(SDA.log_path,
                                            f'cancel_active_send_offers: Отмена активного оффера: {trade}')

                    break
                except Exception:
                    number_of_try += 1
                    print(traceback.format_exc())
                    time.sleep(5)
                    if self.login():
                        number_of_try = 0
                    else:
                        return
                    continue






