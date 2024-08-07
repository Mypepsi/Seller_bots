import re
import json
import time
import pickle
import string
import random
import requests
from lxml import html
from fake_useragent import UserAgent
from bots_libraries.sellpy.logs import Logs
from bots_libraries.steampy.client import SteamClient
from bots_libraries.steampy.models import GameOptions
from bots_libraries.steampy.confirmation import Confirmation
from bots_libraries.sellpy.thread_manager import ThreadManager
from bots_libraries.steampy.confirmation import ConfirmationExecutor


class CreatorSteam(ThreadManager):
    def __init__(self, name):
        super().__init__(name)
        self.ua = UserAgent()


    # region Steam Login
    def steam_login(self, tg_info, global_time):
        Logs.log(f"Steam Login: thread are running", '')
        while True:
            self.update_account_settings_info()
            for acc in self.content_acc_settings_list:
                try:
                    active_session = self.take_session(acc, tg_info)
                    if active_session:
                        try:
                            self.user_agent = self.steamclient.user_agent
                        except:
                            self.user_agent = self.ua.random
                        self.steamclient = SteamClient('', user_agent=self.user_agent)
                        username = acc['username']
                        password = acc['password']
                        steam_id = acc['steam id']
                        shared_secret = acc['shared secret']
                        identity_secret = acc['identity secret']
                        steam_guard = {
                            "steamid": steam_id,
                            "shared_secret": shared_secret,
                            "identity_secret": identity_secret
                        }

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

                        self.make_steam_login(tg_info, username, password, steam_guard)

                except Exception as e:
                    Logs.notify_except(tg_info, f"Steam Login Global Error: {e}", self.steamclient.username)
            time.sleep(global_time)

    def make_steam_login(self, tg_info, username, password, steam_guard):
        number_of_try = 1
        while True:
            try:
                current_timestamp = int(time.time())
                if self.steamclient.username in self.content_acc_data_dict:
                    last_update_time = self.content_acc_data_dict[self.steamclient.username].get('time steam session', 0)
                    difference_to_update = current_timestamp - int(last_update_time)
                    if difference_to_update > self.creator_steam_session_validity_time:
                        self.user_agent = self.steamclient.user_agent
                        self.steamclient.login_steam(username, password, steam_guard, self.steamclient.proxies)
                        Logs.log(f"Steam Login: Authorization was successful", self.steamclient.username)
                        self.handle_doc_in_account_data()
                        self.create_history_doc()
                        time.sleep(10)
                elif self.steamclient.username not in self.content_acc_data_dict:
                    self.steamclient.login_steam(username, password, steam_guard, self.steamclient.proxies)
                    Logs.log(f"Steam Login: Authorization was successful", self.steamclient.username)
                    self.handle_doc_in_account_data()
                    time.sleep(10)
                break
            except:
                if number_of_try == 1:
                    Logs.log(f"Steam Login: Steam Authorization Error", self.steamclient.username)
                    number_of_try += 1
                    time.sleep(30)
                else:
                    Logs.notify(tg_info, f"Steam Login: Not authorized on Steam", self.steamclient.username)
                    break

    def handle_doc_in_account_data(self):
        current_timestamp = int(time.time())
        if self.steamclient.proxies is None:
            proxy_in_accounts_data = None
        else:
            try:
                http_value = self.steamclient.proxies['http']
                match = re.search(r'://([^:]+):([^@]+)@([^:]+):(\d+)', http_value)
                proxy_in_accounts_data = f'{match.group(3)}:{match.group(4)}:{match.group(1)}:{match.group(2)}'
            except:
                proxy_in_accounts_data = 'Error'

        document = self.acc_data_collection.find_one({'username': self.steamclient.username})
        accounts_data = {
            "access token": self.steamclient.access_token,
            "user-agent": self.steamclient.user_agent,
            "proxy": proxy_in_accounts_data
        }
        if document:
            self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                {"$set": {"time steam session": current_timestamp,
                                                          "steam session": pickle.dumps(self.steamclient),
                                                          "steam session data": accounts_data, }})
        else:
            new_doc = {
                "username": self.steamclient.username,
                "time steam session": current_timestamp,
                "steam session": pickle.dumps(self.steamclient),
                "steam session data": accounts_data,
                "steam apikey": "",
                "steam inventory tradable": {},
                "steam inventory full": {},
                "steam inventory phases": {}
            }
            self.acc_data_collection.insert_one(new_doc)

    def create_history_doc(self):
        try:
            collection_name = f'history_{self.steamclient.username}'
            if collection_name not in self.history.list_collection_names():
                self.history.create_collection(collection_name)
        except:
            pass
    # endregion


    def steam_inventory(self, tg_info, global_time):
        Logs.log(f"Steam Inventory: thread are running", '')
        while True:
            for acc in self.content_acc_data_list:
                try:
                    active_session = self.take_session(acc, tg_info)
                    if active_session:
                        self.steamclient.username = acc['username']
                        self.update_db_prices_and_settings()
                        if self.steamclient.username in self.content_acc_data_dict:
                            my_items = self.steamclient.get_inventory_from_link_with_session(
                                self.steamclient.steam_guard['steamid'],
                                GameOptions.CS,
                                proxy=self.steamclient.proxies
                            )
                            all_prices = self.content_database_prices['DataBasePrices']
                            if len(my_items.items()) > 0:
                                current_timestamp = int(time.time())
                                filtered_items_full = {
                                    item_id: {
                                        "asset_id": item_id,
                                        "market_hash_name": item_info["market_hash_name"],
                                        "tradable": item_info.get("tradable", 'Error')
                                    }
                                    for item_id, item_info in my_items.items()
                                }

                                filtered_items_phases = {}
                                for item_id, item_info in my_items.items():
                                    if item_info.get("tradable", 0) != 0:
                                        market_hash_name = item_info["market_hash_name"]
                                        max_price = 0
                                        service_launch_price = None
                                        for price in all_prices:
                                            if market_hash_name in price:
                                                max_price = float(price[market_hash_name]["max_price"])
                                                service_launch_price = price[market_hash_name]["service_max_price"]
                                                break
                                        filtered_items_phases[item_id] = {
                                            "asset_id": item_id,
                                            "market_hash_name": market_hash_name,
                                            "launch_price": max_price,
                                            "service_launch_price": service_launch_price,
                                            "time": current_timestamp
                                        }

                                filtered_items_tradable = {
                                    item_id: {
                                        "asset_id": item_id,
                                        "market_hash_name": item_info["market_hash_name"]
                                    }
                                    for item_id, item_info in my_items.items()
                                    if item_info.get("tradable", 0) != 0
                                }
                                self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                    {"$set": {"steam inventory tradable": filtered_items_tradable,
                                                                              "steam inventory full": filtered_items_full}})

                                try:
                                    inventory_from_mongo = self.content_acc_data_dict[self.steamclient.username]['steam inventory phases']
                                except:
                                    inventory_from_mongo = {}

                                for item_id, item_info in filtered_items_phases.items():
                                    if item_id not in inventory_from_mongo:
                                        inventory_from_mongo[item_id] = {
                                            "asset_id": item_id,
                                            "market_hash_name": item_info["market_hash_name"],
                                            "launch_price": item_info["launch_price"],
                                            "service_launch_price": item_info["service_launch_price"],
                                            "time": current_timestamp
                                        }

                                items_to_remove = [
                                    item_id
                                    for item_id, item_info in inventory_from_mongo.items()
                                    if item_id not in filtered_items_phases and current_timestamp - item_info["time"] >= self.creator_steam_inventory_hashname_validity_time
                                ]
                                for item_id in items_to_remove:
                                    del inventory_from_mongo[item_id]

                                self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                    {"$set": {"steam inventory phases": inventory_from_mongo}})
                except Exception as e:
                    Logs.notify_except(tg_info, f"Steam Inventory Global Error: {e}", acc['username'])
                time.sleep(10)
            time.sleep(global_time)

    def steam_access_token(self, tg_info, global_time):
        Logs.log(f"Steam Access Token: thread are running", '')
        while True:
            self.update_account_data_info()
            for acc in self.content_acc_data_list:
                try:
                    active_session = self.take_session(acc, tg_info)
                    if active_session and self.steamclient.username in self.content_acc_data_dict:
                        url = 'https://steamcommunity.com/pointssummary/ajaxgetasyncconfig'
                        response = self.steamclient._session.get(url, timeout=15)
                        reply = json.loads(response.text)
                        if str(self.steamclient.access_token) != reply['data']['webapi_token']:
                            Logs.notify(tg_info, f"Steam Access Token: Invalid access token", self.steamclient.username)
                            self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                {"$set": {"time steam session": 0}})
                except Exception as e:
                    Logs.notify_except(tg_info, f"Steam Access Token Global Error: {e}", self.steamclient.username)
                time.sleep(10)
            time.sleep(global_time)


    # region Steam Api Key
    def steam_api_key(self, tg_info, global_time):
        Logs.log(f"Steam Api Key: thread are running", '')
        while True:
            for acc in self.content_acc_data_list:
                try:
                    active_session = self.take_session(acc, tg_info)
                    if active_session:
                        api_key_ = 0
                        self.update_account_data_info()
                        if self.steamclient.username in self.content_acc_data_dict:
                            try:
                                response = self.steamclient._session.get('https://steamcommunity.com/dev/apikey', timeout=15)
                                if response.status_code == 200:
                                    api_key_ = self.get_steam_apikey(response.text)
                                    if isinstance(api_key_, bool):
                                        raise Exception
                                    else:
                                        if api_key_ == '00000000000000000000000000000000':
                                            self.revoke_steam_apikey()
                                            raise Exception
                                        old_api_key = self.content_acc_data_dict[self.steamclient.username]['steam apikey']
                                        if api_key_ != '' and api_key_ != '00000000000000000000000000000000' and api_key_ != old_api_key:
                                            self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                                    {"$set": {"steam apikey": api_key_}})
                                else:
                                    continue
                            except:
                                pass
                        if api_key_ == '':
                            self.create_steam_apikey()
                except Exception as e:
                    Logs.notify_except(tg_info, f"Steam Api Key Global Error: {e}", self.steamclient.username)
                time.sleep(10)
            time.sleep(global_time)

    def get_steam_apikey(self, text):
        parsed_body = html.fromstring(text)
        api_key = parsed_body.xpath("//div[@id='bodyContents_ex']/p")
        if len(api_key) == 0:
            return False
        api_key_ = ''
        for p in api_key:
            if 'Key: ' in p.text:
                api_key_ = p.text.replace('Key: ', '')
                return api_key_
        return api_key_

    def revoke_steam_apikey(self):
        url = 'https://steamcommunity.com/dev/revokekey'
        headers = {
            'Cookie': self.get_steam_comm_cookie(),
            'Origin': 'https://steamcommunity.com',
            'Referer': 'https://steamcommunity.com/dev/apikey',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': self.steamclient.user_agent
        }

        sessioon_id = self.get_steam_comm_cookie().split(';')
        for asd in sessioon_id:
            if 'sessionid' in asd:
                sessioon_id = asd.split('=')[1]
                break

        data = {'Revoke': 'Revoke My Steam Web API Key',
                'sessionid': sessioon_id}
        delete_api_key_response = self.steamclient.session.post(url, headers=headers, data=data, timeout=15)
        if delete_api_key_response:
            Logs.log(f"Steam Api Key: Key removed", '')
            self.create_steam_apikey()

    def create_steam_apikey(self):
        headers = {
            'Cookie': self.get_steam_comm_cookie(),
            'Origin': 'https://steamcommunity.com',
            'Referer': 'https://steamcommunity.com/dev/apikey',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': self.steamclient.user_agent
        }
        sessioon_id = self.get_steam_comm_cookie().split(';')
        for asd in sessioon_id:
            if 'sessionid' in asd:
                sessioon_id = asd.split('=')[1]
                break

        json_data = {
            'domain': 'localhost',
            'agreeToTerms': True,
            'sessionid': sessioon_id,
            "request_id": 0
        }

        response = self.steamclient.session.post('https://steamcommunity.com/dev/requestkey', headers=headers,
                                                  data=json_data, timeout=15)

        if response.status_code == 200 and 'requires_confirmation' in response.json():
            request_id = response.json()['request_id']
            confrim_response = self.confrim_request_steam_apikey(request_id)
            if confrim_response:
                headers = {
                    'Cookie': self.get_steam_comm_cookie(),
                    'Origin': 'https://steamcommunity.com',
                    'Referer': 'https://steamcommunity.com/dev/apikey',
                    'X-Requested-With': 'XMLHttpRequest',
                    'User-Agent': self.steamclient.user_agent
                }
                sessioon_id = self.get_steam_comm_cookie().split(';')
                for asd in sessioon_id:
                    if 'sessionid' in asd:
                        sessioon_id = asd.split('=')[1]
                        break

                json_data = {
                    "request_id": request_id,
                    'sessionid': sessioon_id,
                    'domain': ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(7, 15))) + ".com",
                    'agreeToTerms': 'true'
                }

                response_second = self.steamclient.session.post('https://steamcommunity.com/dev/requestkey',
                                                                headers=headers, timeout=15,
                                                                data=json_data).json()

                if 'api_key' in response_second and isinstance(response_second['api_key'], str):
                    Logs.log(f"Steam Api Key: key created", self.steamclient.username)
                    self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                            {"$set": {"steam apikey": response_second['api_key']}})

    def get_steam_comm_cookie(self):
        str = ''
        for cookie in self.steamclient._session.cookies:
            if cookie.domain == 'steamcommunity.com':
                str += cookie.name + '=' + cookie.value + '; '
        return str[0: len(str) - 2]

    def confrim_request_steam_apikey(self, request_id: str):
        try:
            confrirmations = ConfirmationExecutor(self.steamclient.steam_guard['identity_secret'],
                                                  self.steamclient.steam_guard['steamid'],
                                                  self.steamclient.session)
            confirm = confrirmations._fetch_confirmations_page_api_key()['conf']
            need_c = False
            need_data = None
            for c in confirm:
                if c['creator_id'] == request_id:
                    need_c = True
                    need_data = c
                    break

            if need_c:
                jf = Confirmation(f"conf{need_data['id']}", need_data['id'], need_data['nonce'])
                response = confrirmations._send_confirmation_api_key(jf)
                if response['success']:
                    return True
                else:
                    return False
            else:
                return False
        except:
            return False
    # endregion