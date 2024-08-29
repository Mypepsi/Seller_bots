import re
import time
import pickle
import string
import random
from lxml import html
from fake_useragent import UserAgent
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam
from bots_libraries.steampy.client import SteamClient
from bots_libraries.steampy.models import GameOptions
from bots_libraries.steampy.confirmation import Confirmation
from bots_libraries.steampy.confirmation import ConfirmationExecutor


class CreatorSteam(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.ua = UserAgent()

    # region Steam Login
    def steam_login(self):  # Global Function (class_for_single_function)
        Logs.log(f"Steam Login: thread are running", '')
        while True:
            self.update_account_settings_info()
            self.update_account_data_info()
            for acc in self.content_acc_settings_list:
                username = None
                try:
                    if self.take_session(acc):
                        user_agent = self.steamclient.user_agent
                    else:
                        user_agent = self.ua.random
                    self.steamclient = SteamClient('', user_agent=user_agent)
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
                        proxies = {"NoProxy": 1}
                    else:
                        proxy_list = proxy.split(':')
                        proxy_ip = proxy_list[0]
                        proxy_port = proxy_list[1]
                        proxy_login = proxy_list[2]
                        proxy_password = proxy_list[3]
                        proxies = {'http': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}',
                                                    'https': f'http://{proxy_login}:{proxy_password}@{proxy_ip}:{proxy_port}'}

                    self.make_steam_login(username, password, steam_guard, proxies)

                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Steam Login Global Error: {e}", username)
                time.sleep(10)
            time.sleep(self.steam_login_global_time)

    def make_steam_login(self, username, password, steam_guard, proxies):
        number_of_try = 1
        while True:
            try:
                current_timestamp = int(time.time())
                if username in self.content_acc_data_dict:
                    last_update_time = self.content_acc_data_dict[username].get('time steam session', 0)
                    difference_to_update = current_timestamp - int(last_update_time)
                    if difference_to_update > self.steam_session_validity_time:
                        self.steamclient.make_login(username, password, steam_guard, proxies)
                        Logs.log(f"Steam Login: Authorization was successful", username)
                        self.handle_doc_in_account_data()
                        self.create_history_doc()
                elif username not in self.content_acc_data_dict:
                    self.steamclient.make_login(username, password, steam_guard, proxies)
                    Logs.log(f"Steam Login: Authorization was successful", username)
                    self.handle_doc_in_account_data()
                    self.create_history_doc()
                break
            except:
                if number_of_try == 1:
                    Logs.log(f"Steam Login: Steam Authorization Error", username)
                    number_of_try += 1
                    time.sleep(30)
                else:
                    Logs.notify(self.tg_info, f"Steam Login: Not authorized on Steam", username)
                    break

    def handle_doc_in_account_data(self):
        try:
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
                                                              "steam session data": accounts_data}})
            else:
                new_doc = {
                    "username": self.steamclient.username,
                    "time steam session": current_timestamp,
                    "steam session": pickle.dumps(self.steamclient),
                    "steam session data": accounts_data,
                    "steam apikey": '',
                    "steam inventory tradable": {},
                    "steam inventory full": {},
                    "steam inventory phases": {}
                }
                self.acc_data_collection.insert_one(new_doc)
        except Exception as e:
            Logs.notify_except(self.tg_info, f"Steam Login: MongoDB critical request failed: {e}",
                               self.steamclient.username)

    def create_history_doc(self):
        try:
            collection_name = f'history_{self.steamclient.username}'
            if collection_name not in self.history.list_collection_names():
                self.history.create_collection(collection_name)
        except:
            pass
    # endregion

    def steam_inventory(self):  # Global Function (class_for_single_function)
        Logs.log(f"Steam Inventory: thread are running", '')
        while True:
            self.update_account_data_info()
            self.update_database_info(settings=False)
            for acc in self.content_acc_data_list:
                try:
                    if self.take_session(acc):
                        try:
                            my_items = self.steamclient.get_inventory(
                                self.steamclient.steam_guard['steamid'],
                                GameOptions.CS
                            )
                        except:
                            my_items = None
                        all_prices = self.content_database_prices['DataBasePrices']
                        if my_items:
                            current_timestamp = int(time.time())
                            filtered_items_full = {
                                item_id: {
                                    "asset_id": item_id,
                                    "market_hash_name": item_info["market_hash_name"],
                                    "tradable": item_info.get("tradable", 'Error')
                                }
                                for item_id, item_info in my_items.items()
                            }

                            filtered_items_tradable = {
                                item_id: {
                                    "asset_id": item_id,
                                    "market_hash_name": item_info["market_hash_name"]
                                }
                                for item_id, item_info in my_items.items()
                                if item_info.get("tradable", 0) != 0
                            }
                            try:
                                self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                    {"$set": {
                                                                        "steam inventory tradable":
                                                                            filtered_items_tradable,
                                                                        "steam inventory full": filtered_items_full}})
                            except:
                                pass

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

                            for item_id, item_info in filtered_items_phases.items():
                                if item_id not in self.steam_inventory_phases:
                                    self.steam_inventory_phases[item_id] = filtered_items_phases[item_id]

                            items_to_remove = [
                                item_id
                                for item_id, item_info in self.steam_inventory_phases.items()
                                if item_id not in filtered_items_phases and current_timestamp - item_info["time"] >= self.steam_inventory_hashname_validity_time
                            ]
                            for item_id_ in items_to_remove:
                                del self.steam_inventory_phases[item_id_]
                            try:
                                self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                    {"$set": {"steam inventory phases":
                                                                              self.steam_inventory_phases}})
                            except:
                                pass
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Steam Inventory Global Error: {e}", self.steamclient.username)
                time.sleep(10)
            time.sleep(self.steam_inventory_global_time)

    def steam_access_token(self):  # Global Function (class_for_single_function)
        Logs.log(f"Steam Access Token: thread are running", '')
        while True:
            time.sleep(self.steam_access_token_global_time)
            self.update_account_data_info()
            for acc in self.content_acc_data_list:
                try:
                    if self.take_session(acc):
                        try:
                            url = 'https://steamcommunity.com/pointssummary/ajaxgetasyncconfig'
                            reply = self.steamclient.session.get(url, timeout=15).json()
                        except:
                            reply = None
                        if reply and 'data' in reply:
                            if ('webapi_token' in reply['data'] and not reply['data']['webapi_token'] or
                                    ('webapi_token' in reply['data']
                                     and str(self.steamclient.access_token) != reply['data']['webapi_token']) or
                                    isinstance(reply['data'], list)):
                                Logs.notify(self.tg_info, "Steam Access Token: Invalid access token",
                                            self.steamclient.username)
                                try:
                                    self.acc_data_collection.update_one(
                                        {"username": self.steamclient.username},
                                        {"$set": {"time steam session": 0}}
                                    )
                                except:
                                    pass

                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Steam Access Token Global Error: {e}", self.steamclient.username)
                time.sleep(10)
    # region Steam Apikey

    def steam_apikey(self):  # Global Function (class_for_single_function)
        Logs.log(f"Steam Apikey: thread are running", '')
        while True:
            self.update_account_data_info()
            for acc in self.content_acc_data_list:
                try:
                    if self.take_session(acc):
                        try:
                            response = self.steamclient.session.get('https://steamcommunity.com/dev/apikey', timeout=15)
                        except:
                            response = None
                        if response and response.status_code == 200:
                            api_key_ = self.get_steam_apikey(response.text)
                            if isinstance(api_key_, bool):
                                pass
                            elif api_key_ == '':
                                self.create_steam_apikey()
                            elif api_key_ == '00000000000000000000000000000000':
                                self.revoke_steam_apikey()
                            elif api_key_ != self.steamclient._api_key:
                                try:
                                    self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                        {"$set": {"steam apikey": api_key_}})
                                except:
                                    pass
                except Exception as e:
                    Logs.notify_except(self.tg_info, f"Steam Apikey Global Error: {e}", self.steamclient.username)
                time.sleep(10)
            time.sleep(self.steam_apikey_global_time)

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

        session_id = self.steamclient._get_session_id()

        json_data = {'Revoke': 'Revoke My Steam Web API Key',
                'sessionid': session_id}
        try:
            delete_api_key_response = self.steamclient.session.post(url, headers=headers, data=json_data, timeout=15)
        except:
            delete_api_key_response = None
        if delete_api_key_response and delete_api_key_response.status_code == 200:
            Logs.log(f"Steam Apikey: key removed", self.steamclient.username)
            self.create_steam_apikey()

    def create_steam_apikey(self):
        request_key_url = 'https://steamcommunity.com/dev/requestkey'
        headers = {
            'Cookie': self.get_steam_comm_cookie(),
            'Origin': 'https://steamcommunity.com',
            'Referer': 'https://steamcommunity.com/dev/apikey',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': self.steamclient.user_agent
        }

        session_id = self.steamclient._get_session_id()

        json_data = {
            'domain': 'localhost',
            'agreeToTerms': True,
            'sessionid': session_id,
            "request_id": 0
        }
        try:
            response = self.steamclient.session.post(request_key_url, headers=headers, data=json_data, timeout=15).json()
        except:
            response = None

        if response and 'requires_confirmation' in response:
            request_id = response['request_id']
            confirm_response = self.request_to_confirm_steam_apikey(request_id)
            if confirm_response:
                json_data = {
                    "request_id": request_id,
                    'sessionid': session_id,
                    'domain': ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(7, 15))) + ".com",
                    'agreeToTerms': 'true'
                }
                try:
                    response_second = self.steamclient.session.post(request_key_url, headers=headers, timeout=15,
                                                                    data=json_data).json()
                except:
                    response_second = None

                if response_second and 'api_key' in response_second and isinstance(response_second['api_key'], str):
                    Logs.log(f"Steam Apikey: {response_second['api_key']} key created", self.steamclient.username)
                    try:
                        self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                            {"$set": {"steam apikey": response_second['api_key']}})
                    except:
                        pass

    def get_steam_comm_cookie(self):
        str = ''
        for cookie in self.steamclient.session.cookies:
            if cookie.domain == 'steamcommunity.com':
                str += cookie.name + '=' + cookie.value + '; '
        return str[0: len(str) - 2]

    def request_to_confirm_steam_apikey(self, request_id: str):
        try:
            confirmation = ConfirmationExecutor(self.steamclient.steam_guard['identity_secret'],
                                                self.steamclient.steam_guard['steamid'],
                                                self.steamclient.session)
            confirm = confirmation._fetch_confirmations_page_api_key()['conf']
            need_data = None
            for c in confirm:
                if c['creator_id'] == request_id:
                    need_data = c
                    break

            if need_data:
                jf = Confirmation(f"conf{need_data['id']}", need_data['id'], need_data['nonce'])
                response = confirmation._send_confirmation_api_key(jf)
                if response['success']:
                    return True
                else:
                    return False
            else:
                return False
        except:
            return False
    # endregion

