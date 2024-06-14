from bots_libraries.information.logs import Logs
from bots_libraries.information.steam import Steam
from bots_libraries.steampy.confirmation import ConfirmationExecutor
from bots_libraries.steampy.confirmation import Confirmation
from bots_libraries.steampy.models import GameOptions
from lxml import html
from fake_useragent import UserAgent
import string
import pickle
import json
import random
import time
import traceback
import requests

class CreatorSteam(Steam):
    def __init__(self):
        super().__init__()

        self.username_title = 'username'
        self.password_title = 'password'
        self.steam_id_title = 'steam id'
        self.shared_secret_title = 'shared secret'
        self.identity_secret_title = 'identity secret'
        self.proxy_title = 'proxy'
        self.questionable_proxies = {}

        self.ua = UserAgent()


    def steam_login(self):
        number_of_try = 1
        while True:
            try:
                current_timestamp = int(time.time())
                if self.username in self.content_accs_parsed_dict:
                    last_update_time = self.content_accs_parsed_dict[self.username].get('time steam session', 0)
                    difference_to_update = current_timestamp - int(last_update_time)
                    if difference_to_update > self.creator_authorization_time_sleep:
                        self.user_agent = self.steamclient.user_agent
                        self.steamclient.login_steam(self.username, self.password, self.steam_guard, self.proxy)
                        Logs.log(
                            f'{self.username}: Steam authorization is successful')

                        self.accs_parsed_collection.update_one({"username": self.username},
                                                                {"$set": {"time steam session": current_timestamp,
                                                                          "steam session": pickle.dumps(self.steamclient),
                                                                          "steam access token": self.steamclient.access_token}})
                        time.sleep(10)

                elif self.username not in self.content_accs_parsed_dict:
                    self.steamclient.login_steam(self.username, self.password, self.steam_guard, self.proxy)
                    Logs.log(
                        f'{self.username}: Steam authorization is successful')

                    new_doc = {
                            "username": self.username,
                            "time steam session": current_timestamp,
                            "steam session": pickle.dumps(self.steamclient),
                            "steam access token": self.steamclient.access_token,
                            "steam apikey": "",
                            "steam inventory": {},
                            "steam inventory phases": {}
                        }
                    self.accs_parsed_collection.insert_one(new_doc)
                    time.sleep(10)
                break
            except Exception:
                if number_of_try == 1:
                    Logs.log(f'{self.username}: Steam Authorization Error')
                    number_of_try += 1
                    time.sleep(30)
                elif number_of_try == 2:
                    Logs.log(f'{self.username}: Not authorized on steam')
                    self.creator_tg_bot.send_message(self.creator_tg_id,
                                                     (f'Creator: Steam Authorization Error: {self.username}'))
                    break

    def steam_inventory(self):
        if self.username in self.content_accs_parsed_dict:
            try:
                my_items = self.steamclient.get_inventory_from_link_with_session(
                    self.steamclient.steam_guard['steamid'],
                    GameOptions.CS,
                    proxy=self.steamclient.proxies
                )
                if len(my_items.items()) > 0:
                    current_timestamp = int(time.time())

                    filtered_items_phases = {
                        item_id: {
                            "asset_id": item_id,
                            "market_hash_name": item_info["market_hash_name"],
                            "time": current_timestamp
                        }
                        for item_id, item_info in my_items.items()
                        if item_info.get("tradable", 0) != 0
                    }

                    filtered_items = {
                        item_id: {
                            "asset_id": item_id,
                            "market_hash_name": item_info["market_hash_name"]
                        }
                        for item_id, item_info in my_items.items()
                        if item_info.get("tradable", 0) != 0
                    }
                    self.accs_parsed_collection.update_one({"username": self.username},
                                                           {"$set": {"steam inventory": filtered_items}})

                    try:
                        inventory_from_mongo = self.content_accs_parsed_dict[self.username]['steam inventory phases']
                    except:
                        inventory_from_mongo = {}



                    for item_id, item_info in filtered_items_phases.items():
                        if item_id not in inventory_from_mongo:
                            inventory_from_mongo[item_id] = {
                                "asset_id": item_id,
                                "market_hash_name": item_info["market_hash_name"],
                                "time": current_timestamp
                            }

                    items_to_remove = [
                        item_id
                        for item_id, item_info in inventory_from_mongo.items()
                        if item_id not in filtered_items_phases and current_timestamp - item_info["time"] >= self.creator_hashname_difference_time
                    ]
                    for item_id in items_to_remove:
                        del inventory_from_mongo[item_id]

                    self.accs_parsed_collection.update_one({"username": self.username},
                                                           {"$set": {"steam inventory phases": inventory_from_mongo}})
            except:
                Logs.log(f'{self.username}: Steam Inventory Error')
            time.sleep(10)

    def steam_proxy(self):
        self.proxy_for_check = []
        for acc in self.content_accs_parsed_list:
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
                response = requests.get(self.creator_proxy_check_url, proxies=proxy, timeout=10)
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
        if self.username in self.content_accs_parsed_dict:
            try:
                url = 'https://steamcommunity.com/pointssummary/ajaxgetasyncconfig'
                response = self.steamclient._session.get(url, timeout=10)
                reply = json.loads(response.text)
                if str(self.steamclient.access_token) != reply['data']['webapi_token']:
                    self.accs_parsed_collection.update_one({"username": self.username},
                                                           {"$set": {"time steam session": 0}})
                    self.creator_tg_bot.send_message(self.creator_tg_id,
                                                     (f'Creator: Access Token Error: {self.username}'))
                    Logs.log(f'{self.username}: Access Token Error')
            except Exception:
                Logs.log(f'{self.username}: Access Token Response Error')

            time.sleep(10)

    # region steam api key
    def steam_api_key(self):
        api_key_ = 0
        if self.username in self.content_accs_parsed_dict:
            try:
                response = self.steamclient._session.get('https://steamcommunity.com/dev/apikey')    #, headers=headers)
                if response.status_code == 200:
                    api_key_ = self.get_api_key(response.text)
                    if isinstance(api_key_, bool):
                        raise Exception
                    else:
                        if api_key_ == '00000000000000000000000000000000':
                            self.revoke_api_key()
                            raise Exception
                        old_api_key = self.content_accs_parsed_dict[self.username]['steam apikey']
                        if api_key_ != '' and api_key_ != '00000000000000000000000000000000' and api_key_ != old_api_key:
                            self.accs_parsed_collection.update_one({"username": self.username},
                                                                    {"$set": {"steam apikey": api_key_}})
                            raise Exception
                        else:
                            raise Exception
                else:
                    Logs.log(f'{self.username}: Page not found 404')
                    raise Exception
            except Exception:
                pass
        if api_key_ == '':
            self.create_api_key()
        time.sleep(10)

    def create_api_key(self):
        number_of_try = 1
        while True:
            if number_of_try > 3:
                Logs.log(f'{self.username}: Steam ApiKey not created')
                break

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
                                                          data=json_data)

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

                        response_second = self.steamclient.session.post('https://steamcommunity.com/dev/requestkey', headers=headers,
                                                 data=json_data).json()

                        if 'api_key' in response_second and isinstance(response_second['api_key'], str):
                            self.accs_parsed_collection.update_one({"username": self.username},
                                                                    {"$set": {"steam apikey": response_second['api_key']}})
                            break
                        else:
                            Logs.log(f'{self.username}: Failed to create_api_key-2 key')
                            time.sleep(30)


                    else:
                        Logs.log(f'{self.username}: Failed to create_api_key-3 key')
                        time.sleep(30)
            except:
                print(traceback.format_exc())
                pass
            number_of_try += 1

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


    def revoke_api_key(self):
        number_of_try = 0
        while True:
            if number_of_try > 2:
                return False
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
                delete_api_key_response = self.steamclient.session.post(url, headers=headers, data=data)
                if delete_api_key_response:
                    Logs.log(f'{self.username}: Steam ApiKey removed')
                    self.create_api_key()
                    break
            except Exception:
                time.sleep(5)
                number_of_try += 1


    # endregion





