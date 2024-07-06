from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.steam import Steam
from bots_libraries.steampy.confirmation import ConfirmationExecutor
from bots_libraries.steampy.confirmation import Confirmation
from bots_libraries.steampy.models import GameOptions
from lxml import html
import string
import re
import pickle
import json
import random
import time
import traceback
import requests

class CreatorSteam(Steam):
    def __init__(self):
        super().__init__()

    #region login in steam and create history collections and accounts data docs
    def steam_login(self):
        number_of_try = 1
        while True:
            try:
                current_timestamp = int(time.time())
                if self.steamclient.username in self.content_acc_data_dict:
                    last_update_time = self.content_acc_data_dict[self.steamclient.username].get('time steam session', 0)
                    difference_to_update = current_timestamp - int(last_update_time)
                    if difference_to_update > self.creator_authorization_time_sleep:
                        self.user_agent = self.steamclient.user_agent
                        self.steamclient.login_steam(self.steamclient.username, self.steamclient.password, self.steamclient.steam_guard, self.steamclient.proxies)
                        Logs.log(
                            f'{self.steamclient.username}: Steam authorization is successful')
                        self.handle_account_data_doc()
                        self.create_history_docs()
                        time.sleep(10)

                elif self.steamclient.username not in self.content_acc_data_dict:
                    self.steamclient.login_steam(self.steamclient.username, self.steamclient.password, self.steamclient.steam_guard, self.steamclient.proxies)
                    Logs.log(
                        f'{self.steamclient.username}: Steam authorization is successful')

                    self.handle_account_data_doc()
                    time.sleep(10)
                break
            except Exception:
                if number_of_try == 1:
                    Logs.log(f'{self.steamclient.username}: Steam Authorization Error')
                    number_of_try += 1
                    time.sleep(30)
                elif number_of_try == 2:
                    Logs.log(f'{self.steamclient.username}: Not authorized on steam')
                    self.creator_tg_bot.send_message(self.creator_tg_id,
                                                     (f'Creator: Steam Authorization Error: {self.steamclient.username}'))
                    break

    def create_history_docs(self):
        try:
            collection_name = f'history_{self.steamclient.username}'
            if collection_name not in self.history.list_collection_names():
                self.history.create_collection(collection_name)
        except:
            pass

    def handle_account_data_doc(self):
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


    # endregion

    def steam_inventory(self):
        self.update_db_prices_and_setting()
        if self.steamclient.username in self.content_acc_data_dict:
            try:
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
                        if item_id not in filtered_items_phases and current_timestamp - item_info["time"] >= self.creator_hashname_difference_time
                    ]
                    for item_id in items_to_remove:
                        del inventory_from_mongo[item_id]

                    self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                           {"$set": {"steam inventory phases": inventory_from_mongo}})
            except:
                Logs.log(f'{self.steamclient.username}: Steam Inventory Error')
            time.sleep(10)

    def steam_proxy(self):
        self.update_account_data_info()
        self.proxy_for_check = []
        for acc in self.content_acc_data_list:
            steam_session = acc['steam session']
            self.take_session(steam_session)
            self.proxy_for_check.append(self.steamclient.proxies)
        unique_proxy_for_check = []
        for proxy in self.proxy_for_check:
            if proxy not in unique_proxy_for_check and proxy is not None:
                unique_proxy_for_check.append(proxy)
        self.proxy_for_check = unique_proxy_for_check
        for proxy in self.proxy_for_check:
            try:
                proxy_ip = proxy['http'].split('://')[1].split('@')[1].split(':')[0]
            except:
                proxy_ip = proxy
            try:
                response = requests.get(self.creator_proxy_check_url, proxies=proxy, timeout=20)
                if response.status_code == 200:
                    try:
                        del self.questionable_proxies[proxy_ip]
                    except KeyError:
                        pass
            except Exception:
                if proxy_ip in self.questionable_proxies:
                    self.questionable_proxies[proxy_ip] += 1
                    if self.questionable_proxies[proxy_ip] == 3:
                        self.creator_tg_bot.send_message(self.creator_tg_id, (f'Creator: Proxy Error: {proxy_ip}'))
                else:
                    self.questionable_proxies[proxy_ip] = 1
                Logs.log(f'Proxy Error: {proxy_ip}')
            time.sleep(10)
        Logs.log(
            f'Steam Proxy: All proxies checked ({len(self.proxy_for_check)} proxies in MongoDB)')

    def steam_access_token(self):
        if self.steamclient.username in self.content_acc_data_dict:
            try:
                url = 'https://steamcommunity.com/pointssummary/ajaxgetasyncconfig'
                response = self.steamclient._session.get(url, timeout=20)
                reply = json.loads(response.text)
                if str(self.steamclient.access_token) != reply['data']['webapi_token']:
                    self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                           {"$set": {"time steam session": 0}})
                    self.creator_tg_bot.send_message(self.creator_tg_id,
                                                     (f'Creator: Access Token Error: {self.steamclient.username}'))
                    Logs.log(f'{self.steamclient.username}: Access Token Error')
            except Exception:
                Logs.log(f'{self.steamclient.username}: Access Token Response Error')

            time.sleep(10)

    # region steam api key
    def steam_api_key(self):
        api_key_ = 0
        if self.steamclient.username in self.content_acc_data_dict:
            try:
                response = self.steamclient._session.get('https://steamcommunity.com/dev/apikey', timeout=20)
                if response.status_code == 200:
                    api_key_ = self.get_api_key(response.text)
                    if isinstance(api_key_, bool):
                        raise Exception
                    else:
                        if api_key_ == '00000000000000000000000000000000':
                            self.revoke_api_key()
                            raise Exception
                        old_api_key = self.content_acc_data_dict[self.steamclient.username]['steam apikey']
                        if api_key_ != '' and api_key_ != '00000000000000000000000000000000' and api_key_ != old_api_key:
                            self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                    {"$set": {"steam apikey": api_key_}})
                else:
                    Logs.log(f'{self.steamclient.username}: Page not found 404')
                    raise Exception
            except Exception:
                Logs.log(f'{self.steamclient.username}: steam_api_key error')
        if api_key_ == '':
            self.create_api_key()
        time.sleep(10)

    def revoke_api_key(self):
        try:
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
            delete_api_key_response = self.steamclient.session.post(url, headers=headers, data=data, timeout=20)
            if delete_api_key_response:
                Logs.log(f'{self.steamclient.username}: Steam ApiKey removed')
                self.create_api_key()
        except Exception:
            Logs.log(f'{self.steamclient.username}: error revoke_api_key')

    def create_api_key(self):
        try:
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
                                                      data=json_data, timeout=20)

            if response.status_code == 200 and 'requires_confirmation' in response.json():
                request_id = response.json()['request_id']
                confrim_response = self.confrim_request_api_key(request_id)
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
                                                                    headers=headers, timeout=20,
                                                                    data=json_data).json()

                    if 'api_key' in response_second and isinstance(response_second['api_key'], str):
                        self.acc_data_collection.update_one({"username": self.steamclient.username},
                                                                {"$set": {"steam apikey": response_second['api_key']}})
                    else:
                        Logs.log(f'{self.steamclient.username}: Failed to create_api_key-2 key')
                else:
                    Logs.log(f'{self.steamclient.username}: Failed to create_api_key-3 key')
        except:
            Logs.log(f'{self.steamclient.username}: Steam ApiKey not created')
            pass

    def confrim_request_api_key(self, request_id: str):
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
            print(traceback.format_exc())
            return False

    def get_steam_comm_cookie(self):
        str = ''
        for cookie in self.steamclient._session.cookies:
            if cookie.domain == 'steamcommunity.com':
                str += cookie.name + '=' + cookie.value + '; '
        return str[0: len(str) - 2]

    def get_api_key(self, text):
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

    # endregion





