import bs4
import rsa
import json
import base64
import decimal
import requests
from lxml import html
from typing import List, Union
import urllib.parse as urlparse
from bots_libraries.steampy import guard
from bots_libraries.steampy.confirmation import ConfirmationExecutor
from bots_libraries.steampy.steam_auth.auth.schemas import FinalizeLoginStatus
from bots_libraries.steampy.steam_auth.pb2.enums_pb2 import ESessionPersistence
from bots_libraries.steampy.models import Asset, TradeOfferState, SteamUrl, GameOptions
from bots_libraries.steampy.exceptions import SevenDaysHoldException, LoginRequired, ApiException, InvalidCredentials
from bots_libraries.steampy.utils import (
    parse_price,
    text_between,
    texts_between,
    get_description_key,
    get_key_value_from_url,
    account_id_to_steam_id,
    merge_items_with_descriptions_from_offer,
    merge_items_with_descriptions_from_inventory,
)
from bots_libraries.steampy.steam_auth.pb2.steammessages_auth.steamclient_pb2 import (
    EAuthSessionGuardType,
    EAuthTokenPlatformType,
    CAuthentication_AllowedConfirmation,
    CAuthentication_PollAuthSessionStatus_Request,
    CAuthentication_PollAuthSessionStatus_Response,
    CAuthentication_GetPasswordRSAPublicKey_Request,
    CAuthentication_GetPasswordRSAPublicKey_Response,
    CAuthentication_BeginAuthSessionViaCredentials_Request,
    CAuthentication_BeginAuthSessionViaCredentials_Response,
    CAuthentication_UpdateAuthSessionWithSteamGuardCode_Request,
)


def login_required(func):
    def func_wrapper(self, *args, **kwargs):
        if not self.was_login_executed:
            raise LoginRequired('Use login method first')
        else:
            return func(self, *args, **kwargs)
    return func_wrapper


class SteamClient:
    def __init__(self, api_key: str, username: str = None, password: str = None, steam_guard: dict = None, user_agent: str = None) -> None:
        if user_agent is None:
            self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        else:
            self.user_agent = user_agent
        self._api_key = api_key
        self._session = requests.session()
        self._session.headers.update({
            'User-Agent': self.user_agent
        })
        self.steam_guard = steam_guard
        self.was_login_executed = False
        self.username = username
        self._password = password
        # self.market = SteamMarket(self._session)
        # self.chat = SteamChat(self._session)

    def make_login(self, username: str, password: str, steam_guard: dict, proxy: dict):
        self.steam_guard = guard.load_steam_guard(steam_guard)
        self.username = username
        self._password = password
        if 'NoProxy' in proxy:
            self.proxies = None
        else:
            self.proxies = proxy
            self._session.proxies.update(self.proxies)

        if not self._session.cookies.get_dict().get('sessionid'):
            self._session.get('https://steamcommunity.com', timeout=15)

        message = CAuthentication_GetPasswordRSAPublicKey_Request(
            account_name=username,
        )
        rsa_data = self._fetch_rsa_params(message)
        encrypted_password = self._encrypt_password_new(password, rsa_data)
        message = CAuthentication_BeginAuthSessionViaCredentials_Request(
            account_name=username,
            encrypted_password=encrypted_password,
            encryption_timestamp=rsa_data.timestamp,
            remember_login=True,
            platform_type=EAuthTokenPlatformType.k_EAuthTokenPlatformType_WebBrowser,
            website_id='Community',
            persistence=ESessionPersistence.k_ESessionPersistence_Persistent,
        )
        kjee = {
            "input_protobuf_encoded": base64.b64encode(message.SerializeToString())
        }
        response = self._begin_auth_session(kjee)
        steam_id = response.steamid
        if response.allowed_confirmations:
            if self._is_twofactor_required(response.allowed_confirmations[0]):
                self.get_server_time()
                one_time_code = guard.generate_one_time_code(steam_guard['shared_secret'])

                message = CAuthentication_UpdateAuthSessionWithSteamGuardCode_Request(
                    client_id=response.client_id,
                    steamid=response.steamid,
                    code=one_time_code,
                    code_type=EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceCode,
                )

                kjee = {
                    "input_protobuf_encoded": base64.b64encode(message.SerializeToString())
                }
                self._update_auth_session(kjee)

        # PollAuthSessionStatus
        message = CAuthentication_PollAuthSessionStatus_Request(
            client_id=response.client_id,
            request_id=response.request_id,
        )
        kjee = {
            "input_protobuf_encoded": base64.b64encode(message.SerializeToString())
        }
        response = self._poll_auth_session_status(kjee)
        kjee = {
            'nonce': response.refresh_token,
            'sessionid': self._get_session_id(),
            'redir': 'https://steamcommunity.com/login/home/?goto='
        }
        tokens = self._finalize_login(kjee)
        for token in tokens.transfer_info:
            url = token.url
            nonce = token.params.nonce
            auth = token.params.auth
            steamid = steam_id
            data = {
                'nonce': nonce,
                'auth': auth,
                'steamID': str(steamid)
            }
            self._set_token(url, data)
        access_token = self._session.cookies.get(name='steamLoginSecure', domain='steamcommunity.com').split('%7C%7C')[1]
        self.access_token = access_token
        self.was_login_executed = True

    @login_required
    def get_inventory(self, partner_steam_id: str, game: GameOptions, merge: bool = True,
                      count: int = 5000) -> dict:
        url = '/'.join([SteamUrl.COMMUNITY_URL, 'inventory', partner_steam_id, game.app_id, game.context_id])
        params = {'l': 'english',
                  'count': count}
        response_dict = self._session.get(url, params=params, timeout=15).json()
        if response_dict['success'] != 1:
            raise ApiException('Success value should be 1.')
        if merge:
            return merge_items_with_descriptions_from_inventory(response_dict, game)
        return response_dict

    @staticmethod
    def get_steam_id_from_url(trade_offer_url):
        partner_account_id = get_key_value_from_url(trade_offer_url, 'partner', True)
        partner_steam_id = account_id_to_steam_id(partner_account_id)
        return partner_steam_id

    @login_required
    def make_trade_offer(self, items_from_me: List[Asset], items_from_them: List[Asset],
                         trade_offer_url: str, message: str = '', case_sensitive: bool = True):
        token = get_key_value_from_url(trade_offer_url, 'token', case_sensitive)
        partner_account_id = get_key_value_from_url(trade_offer_url, 'partner', case_sensitive)
        partner_steam_id = account_id_to_steam_id(partner_account_id)
        offer = self._create_offer_dict(items_from_me, items_from_them)
        session_id = self._get_session_id()
        url = SteamUrl.COMMUNITY_URL + '/tradeoffer/new/send'
        server_id = 1
        trade_offer_create_params = {'trade_offer_access_token': token}
        params = {
            'sessionid': session_id,
            'serverid': server_id,
            'partner': partner_steam_id,
            'tradeoffermessage': message,
            'json_tradeoffer': json.dumps(offer),
            'captcha': '',
            'trade_offer_create_params': json.dumps(trade_offer_create_params)
        }
        headers = {
            'Referer': SteamUrl.COMMUNITY_URL + urlparse.urlparse(trade_offer_url).path,
            'Origin': SteamUrl.COMMUNITY_URL,
            'Host': 'steamcommunity.com'
        }

        try:
            response = self._session.post(url, data=params, headers=headers, timeout=15).json()
            return response
        except:
            return None

    @login_required
    def confirm_trade_offer(self, trade_offer_id: str):
        try:
            self._confirm_transaction(trade_offer_id)
        except:
            pass

    def get_trade_offers(self,
                         get_sent_offers=0,
                         get_received_offers=0,
                         get_descriptions=0,
                         active_only=0,
                         historical_only=0,
                         language: str = 'english',
                         time_historical_cutoff: str = ''):
        params = {'access_token': self.access_token,
                  'get_sent_offers': get_sent_offers,
                  'get_received_offers': get_received_offers,
                  'get_descriptions': get_descriptions,
                  'language': language,
                  'active_only': active_only,
                  'historical_only': historical_only,
                  'time_historical_cutoff': time_historical_cutoff}
        try:
            response = self.api_call('GET', 'IEconService', 'GetTradeOffers', 'v1', params).json()
            return response
        except:
            return None

    def get_trade_offer(self, trade_offer_id: str):
        params = {'access_token': self.access_token,
                  'tradeofferid': trade_offer_id,
                  'language': 'english'}
        try:
            response = self.api_call('GET', 'IEconService', 'GetTradeOffer', 'v1', params).json()
            return response
        except:
            return None

    @login_required
    def cancel_trade_offer(self, trade_offer_id: str):
        url = 'https://steamcommunity.com/tradeoffer/' + trade_offer_id + '/cancel'
        try:
            response = self._session.post(url, data={'sessionid': self._get_session_id()}, timeout=15).json()
            return response
        except:
            return None

    @login_required
    def accept_trade_offer(self, trade_offer_id: str, steam_id: str):
        accept_url = SteamUrl.COMMUNITY_URL + '/tradeoffer/' + trade_offer_id + '/accept'
        params = {'sessionid': self._get_session_id(),
                  'tradeofferid': trade_offer_id,
                  'serverid': '1',
                  'partner': steam_id,
                  'captcha': ''}
        headers = {'Referer': self._get_trade_offer_url(trade_offer_id)}
        try:
            response = self._session.post(accept_url, data=params, headers=headers, timeout=15).json()
            if response.get('needs_mobile_confirmation', False):
                self._confirm_transaction(trade_offer_id)
        except:
            return None
        return trade_offer_id

    def get_trade_offers_summary(self) -> dict:
        params = {'key': self._api_key}
        return self.api_call('GET', 'IEconService', 'GetTradeOffersSummary', 'v1', params).json()

    def get_trade_history(self,
                          max_trades=100,
                          start_after_time=None,
                          start_after_tradeid=None,
                          get_descriptions=True,
                          navigating_back=True,
                          include_failed=True,
                          include_total=True) -> dict:
        params = {
            'key': self._api_key,
            'max_trades': max_trades,
            'start_after_time': start_after_time,
            'start_after_tradeid': start_after_tradeid,
            'get_descriptions': get_descriptions,
            'navigating_back': navigating_back,
            'include_failed': include_failed,
            'include_total': include_total
        }
        response = self.api_call('GET', 'IEconService', 'GetTradeHistory', 'v1', params).json()
        return response

    @login_required
    def get_trade_receipt(self, trade_id: str) -> list:
        html = self._session.get("https://steamcommunity.com/trade/{}/receipt".format(trade_id), timeout=15).content.decode()
        items = []
        for item in texts_between(html, "oItem = ", ";\r\n\toItem"):
            items.append(json.loads(item))
        return items

    @login_required
    def decline_trade_offer(self, trade_offer_id: str) -> dict:
        url = 'https://steamcommunity.com/tradeoffer/' + trade_offer_id + '/decline'
        response = self._session.post(url, data={'sessionid': self._get_session_id()}, timeout=15).json()
        return response

    def get_profile(self, steam_id: str) -> dict:
        params = {'steamids': steam_id, 'key': self._api_key}
        response = self.api_call('GET', 'ISteamUser', 'GetPlayerSummaries', 'v0002', params)
        data = response.json()
        return data['response']['players'][0]

    def get_friend_list(self, steam_id: str, relationship_filter: str = "all") -> dict:
        params = {
            'key': self._api_key,
            'steamid': steam_id,
            'relationship': relationship_filter
        }
        resp = self.api_call("GET", "ISteamUser", "GetFriendList", "v1", params)
        data = resp.json()
        return data['friendslist']['friends']

    @login_required
    def is_session_alive(self):
        steam_login = self.username
        main_page_response = self._session.get(SteamUrl.COMMUNITY_URL, timeout=15)
        return steam_login.lower() in main_page_response.text.lower()

    def api_call(self, request_method: str, interface: str, api_method: str, version: str,
                 params: dict = None) -> requests.Response:
        url = '/'.join([SteamUrl.API_URL, interface, api_method, version])
        if request_method == 'GET':
            if self.proxies is None:
                response = requests.get(url, params=params, timeout=15)
            else:
                response = requests.get(url, params=params, proxies=self.proxies, timeout=15)
        else:
            if self.proxies is None:
                response = requests.post(url, data=params, timeout=15)
            else:
                response = requests.post(url, data=params, proxies=self.proxies, timeout=15)

        if self.is_invalid_api_key(response):
            raise InvalidCredentials('Invalid API key')
        return response

    @staticmethod
    def is_invalid_api_key(response: requests.Response) -> bool:
        msg = 'Access is denied. Retrying will not help. Please verify your <pre>key=</pre> parameter'
        return msg in response.text

    @staticmethod
    def get_api_key(text):
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

    @property
    def session(self):
        return self._session

    def _get_session_id(self) -> str:
        return self._session.cookies.get('sessionid', domain='steamcommunity.com')


    @login_required
    def get_escrow_duration(self, trade_offer_url: str) -> int:
        headers = {'Referer': SteamUrl.COMMUNITY_URL + urlparse.urlparse(trade_offer_url).path,
                   'Origin': SteamUrl.COMMUNITY_URL}
        response = self._session.get(trade_offer_url, headers=headers, timeout=15).text
        my_escrow_duration = int(text_between(response, "var g_daysMyEscrow = ", ";"))
        their_escrow_duration = int(text_between(response, "var g_daysTheirEscrow = ", ";"))
        return max(my_escrow_duration, their_escrow_duration)

    def get_cookies(self):
        dictri = self._session.cookies.get_dict()
        str = ''
        for key in dictri:
            str += key + '=' + dictri[key] + '; '
        return str[0: len(str) - 2]

    def get_server_time(self) -> int:
        response = self._session.post('https://api.steampowered.com/ITwoFactorService/QueryTime/v0001', timeout=15)
        data = response.json()
        return int(data['response']['server_time'])

    @login_required
    def get_wallet_balance(self, convert_to_decimal: bool = True) -> Union[str, decimal.Decimal]:
        url = SteamUrl.STORE_URL + '/account/history/'
        response = self._session.get(url, timeout=15)
        response_soup = bs4.BeautifulSoup(response.text, "html.parser")
        balance = response_soup.find(id='header_wallet_balance').string
        if convert_to_decimal:
            return parse_price(balance)
        else:
            return balance

    def _fetch_trade_partner_id(self, trade_offer_id: str) -> str:
        url = self._get_trade_offer_url(trade_offer_id)
        offer_response_text = self._session.get(url, timeout=15).text

        if 'You have logged in from a new device. In order to protect the items' in offer_response_text:
            raise SevenDaysHoldException("Account has logged in a new device and can't trade for 7 days")
        return 'qwerty'

    def _confirm_transaction(self, trade_offer_id: str) -> dict:
        confirmation_executor = ConfirmationExecutor(self.steam_guard['identity_secret'], self.steam_guard['steamid'],
                                                     self._session)
        return confirmation_executor.send_trade_allow_request(trade_offer_id)

    @staticmethod
    def _create_offer_dict(items_from_me: List[Asset], items_from_them: List[Asset]) -> dict:
        return {
            'newversion': True,
            'version': 4,
            'me': {
                'assets': [asset.to_dict() for asset in items_from_me],
                'currency': [],
                'ready': False
            },
            'them': {
                'assets': [asset.to_dict() for asset in items_from_them],
                'currency': [],
                'ready': False
            }
        }

    @staticmethod
    def _get_trade_offer_url(trade_offer_id: str) -> str:
        return SteamUrl.COMMUNITY_URL + '/tradeoffer/' + trade_offer_id

    def _set_token(self, url: str, data) -> None:
        self._session.post(url, data=data)

    def _finalize_login(self, data) -> FinalizeLoginStatus:
        response = self._session.post('https://login.steampowered.com/jwt/finalizelogin', data=data, timeout=15)
        return FinalizeLoginStatus.parse_raw(response.content)

    def _poll_auth_session_status(self, data) -> CAuthentication_PollAuthSessionStatus_Response:
        response = self._session.post('https://api.steampowered.com/IAuthenticationService/PollAuthSessionStatus/v1', data=data, timeout=15)
        return CAuthentication_PollAuthSessionStatus_Response.FromString(response.content)

    def _update_auth_session(self, data) -> None:
        self._session.post('https://api.steampowered.com/IAuthenticationService/UpdateAuthSessionWithSteamGuardCode/v1', data=data, timeout=15)

    def _is_twofactor_required(self, confirmation: CAuthentication_AllowedConfirmation) -> bool:
        return confirmation.confirmation_type == EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceCode

    def _begin_auth_session(self, data) -> CAuthentication_BeginAuthSessionViaCredentials_Response:
        response = self._session.post('https://api.steampowered.com/IAuthenticationService/BeginAuthSessionViaCredentials/v1', data=data, timeout=15)
        return CAuthentication_BeginAuthSessionViaCredentials_Response.FromString(response.content)

    def _fetch_rsa_params(self, message, current_number_of_repetitions: int = 0):
        maximal_number_of_repetitions = 5
        try:
            key_response = self._session.get(
                'https://api.steampowered.com/IAuthenticationService/GetPasswordRSAPublicKey/v1',
                params={'input_protobuf_encoded': str(base64.b64encode(message.SerializeToString()), 'utf8')}, timeout=15)

            return CAuthentication_GetPasswordRSAPublicKey_Response.FromString(key_response.content)

        except:
            if current_number_of_repetitions < maximal_number_of_repetitions:
                return self._fetch_rsa_params(message, current_number_of_repetitions + 1)
            else:
                raise ValueError('Could not obtain rsa-key')

    def _encrypt_password_new(self, password, keys: CAuthentication_GetPasswordRSAPublicKey_Response) -> str:
        publickey_exp = int(keys.publickey_exp, 16)  # type:ignore
        publickey_mod = int(keys.publickey_mod, 16)  # type:ignore
        public_key = rsa.PublicKey(
            n=publickey_mod,
            e=publickey_exp,
        )
        encrypted_password = rsa.encrypt(
            message=password.encode('ascii'),
            pub_key=public_key,
        )
        return str(base64.b64encode(encrypted_password), 'utf8')

    @staticmethod
    def _filter_non_active_offers(offers_response):
        offers_received = offers_response['response'].get('trade_offers_received', [])
        offers_sent = offers_response['response'].get('trade_offers_sent', [])
        offers_response['response']['trade_offers_received'] = list(
            filter(lambda offer: offer['trade_offer_state'] == TradeOfferState.Active, offers_received))
        offers_response['response']['trade_offers_sent'] = list(
            filter(lambda offer: offer['trade_offer_state'] == TradeOfferState.Active, offers_sent))
        return offers_response
