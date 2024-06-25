from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.mongo import Mongo
from bots_libraries.creator.creator_steam import Steam
from bots_libraries.steampy.confirmation import ConfirmationExecutor
from bots_libraries.steampy.confirmation import Confirmation
from bots_libraries.steampy.models import GameOptions
from bots_libraries.steampy.client import Asset
from lxml import html
from fake_useragent import UserAgent
import string
import pickle
import json
import io
import random
import time
import traceback
import requests


class TMSteam(Steam):
    def __init__(self):
        super().__init__()
        self.acc_history_collection = None

    def request_give_p2p_all(self, username):
        try:
            url = f'https://market.csgo.com/api/v2/trade-request-give-p2p-all?key={self.steamclient.tm_api}'
            response = requests.get(url, timeout=10)
            response_data = response.json()
            return response_data
        except Exception:
            return None

    def make_steam_offer(self, response_data_offer, send_offers, inventory_phases):
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
            time.sleep(3)
            if 'tradeofferid' in steam_response:
                self.handle_tm_history_doc(inventory_phases, send_offers, assets, names, msg, steam_response)
                Logs.log(f"{self.steamclient.username}: Steam Trade Sent: {names}")
            else:
                Logs.log(f"{self.steamclient.username}: Steam Trade Error : {names}")
        except Exception as e:
            Logs.log(f'Error when sending a steam trade: {e}')

    def handle_tm_history_doc(self, inventory_phases, send_offers, assets_list, name_list, msg, steam_response):
        current_timestamp = int(time.time())
        for asset in assets_list:
            name = ''
            for item in inventory_phases.values():
                if item['asset_id'] == asset:
                    name = item['market_hash_name']
                    name_list.append(name)
                    break
            name_exists = any(entry.get('site id') == msg for entry in send_offers)
            if name_exists:
                self.acc_history_collection.update_one(
                    {
                        "$and": [
                            {"asset id": asset},
                            {"site id": msg}
                        ]
                    },
                    {
                        "$set": {
                            "steam status": 'again sent',
                            "sent time": current_timestamp,
                            "trade id": steam_response['tradeofferid']
                        }
                    }
                )
            else:
                data_append = {
                    "name": name,
                    "price": 0,
                    "site": "tm",
                    "steam status": 'sent',
                    "site status": 'active_deal',
                    "time": current_timestamp,
                    "site id": msg,
                    "asset id": asset,
                    "trade id": steam_response['tradeofferid'],
                    "sent time": current_timestamp
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
                        for offer in send_offers:
                            if msg in offer.values() and msg not in unique_msg_in_send_offers:
                                unique_msg_in_send_offers.append(msg)
                                trade_id = offer['trade id']
                                response_steam_trade_offer = self.steamclient.get_trade_offer_state(trade_id)

                                if not isinstance(response_steam_trade_offer, dict):
                                    continue

                                if 'response' in response_steam_trade_offer and 'offer' in response_steam_trade_offer['response']:
                                    offer_status = response_steam_trade_offer['response']['offer']['trade_offer_state']
                                else:
                                    continue

                                if int(offer_status) not in [1, 4, 8, 10]:
                                    continue
                            self.make_steam_offer(response_data['offers'][i],send_offers, acc_data_inventory_phases)
                    except:
                        Logs.log('Error in tm trades')
            elif 'error' in response_data:
                if response_data['error'] == 'nothing':
                    Logs.log('There is no need to transfer anything')
            time.sleep(time_sleep)









        # if str(trade_id) in sent_trade_ready:
        #     continue

    # trade_ready
    # for i in range(len(response_data['offers'])):
    #     msg = response_data['offers'][i]['tradeoffermessage']
    #     for offer in sent_offers:
    #         trade_id = offer['trade_id']
    #         data_text = offer['text']
    #         if msg == data_text:
    #             try:
    #                 url = f'https://market.csgo.com/api/v2/trade-ready?key={self.steamclient.tm_api}&tradeoffer={trade_id}'
    #                 response_ = requests.get(url, timeout=10)
    #                 response_data_ = response_.json()
    #             except Exception:
    #                 break
    #
    #             if 'success' in response_data_ and response_data_['success']:
    #                 # запись в подтвержденные трейды
    #
    #                 pass
    #
    #             break
    #         else:
    #             continue

















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



    def add_to_sale(self, acc_info, time_sleep):
        while True:
            self.update_account_data_info()
            self.update_db_prices_and_setting()
            username = ''
            acc_data_inventory = []
            try:
                username = acc_info['username']
                acc_data_inventory = acc_info['steam inventory tradable']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
            except:
                Logs.log('Error during taking a session')
            filtered_inventory = self.get_and_filtered_inventory(acc_data_inventory)

            items = {}
            if 'items' in response and type(response['items']) == list:
                for i in range(len(response['items'])):
                    if response['items'][i]['tradable'] != 1:
                        continue
                    item_name = response['items'][i]['market_hash_name']
                    item_id = response['items'][i]['id']
                    if item_name not in items:
                        items.update({item_name: [item_id]})
                    else:
                        items[item_name].append(item_id)
            else:
                return
            if len(items) == 0:
                return



            # выставление по списку
            if add_to_sale_mode == 2:
                mode_2_items = {}
                listed_items = Bot.get_listed_items()
                for i in range(len(listed_items)):
                    if listed_items[i] in items:
                        mode_2_items.update({listed_items[i]: items[listed_items[i]]})
                items = mode_2_items

            # выставление
            if len(items) == 0:
                return
            else:
                # получение цен для выставления
                self.db_lock.acquire()
                prices = dict(self.db)
                self.db_lock.release()

                # шаги для выставления
                add_to_sale_step_1 = Settings.return_setting(
                    self.general_settings_path, self.add_to_sale_step_1_name, 'float')
                add_to_sale_step_2 = Settings.return_setting(
                    self.general_settings_path, self.add_to_sale_step_2_name, 'float')
                add_to_sale_step_3 = Settings.return_setting(
                    self.general_settings_path, self.add_to_sale_step_3_name, 'float')

                currency_type = Settings.return_setting(
                    self.price_calculate_path, 'rate type tm', 'int')

                currency = Settings.return_setting(
                    self.price_calculate_path, 'currency tm', 'float')
                if currency_type == 1:
                    currency = 1 / currency

                for key in items:
                    item_name = key
                    try:
                        item_price = prices[item_name]['price']['max_price']
                    except KeyError:
                        continue

                    if item_price != 0:
                        if 0 < item_price <= 15:
                            item_price = item_price * add_to_sale_step_1
                        elif 15 < item_price <= 150:
                            item_price = item_price * add_to_sale_step_2
                        else:
                            item_price = item_price * add_to_sale_step_3

                        # умножение или деление на валюту цены и выставление
                        sale_price = int(item_price * currency * 100)
                        # выставление на продажу
                        for i in range(len(items[key])):
                            url = self.market_add_to_sale_url + items[key][i].replace('&', '%26') + f'&price={sale_price}'
                            response = self.request(url, 'get')
                            if response['success']:
                                try:
                                    response = response['rs'].json()
                                    if 'success' in response and response['success']:
                                        self.logs.write_log(self.logs_path, 'add to sale', f'предмет {key} '
                                                                                           f'выставлен за {round(sale_price / 100, 2)} RUB')
                                except Exception:
                                    self.logs.write_log(self.logs_path, 'add to sale', f'ошибка json')
                            else:
                                self.logs.write_log(self.logs_path,
                                                    'add to sale',
                                                    f'ошибка маркета, не удалось выставить предмет.')

                    else:
                        continue










