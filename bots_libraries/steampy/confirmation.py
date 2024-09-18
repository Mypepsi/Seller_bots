import enum
import json
import time
import requests
from typing import List
from bs4 import BeautifulSoup
from bots_libraries.steampy import guard
from bots_libraries.steampy.exceptions import ConfirmationExpected


class Confirmation:
    def __init__(self, _id, data_confid, data_key, trade_id=None):
        self.id = _id.split('conf')[1]
        self.data_confid = data_confid
        self.data_key = data_key
        self.trade_id = trade_id


class Tag(enum.Enum):
    CONF = 'conf'
    DETAILS = 'details'
    ALLOW = 'allow'
    CANCEL = 'cancel'
    ACCEPT = 'accept'


class ConfirmationExecutor:
    CONF_URL = "https://steamcommunity.com/mobileconf"

    def __init__(self, identity_secret: str, my_steam_id: str, session: requests.session) -> None:
        self._my_steam_id = my_steam_id
        self._identity_secret = identity_secret
        self._session = session

        self.count_market_conf = 0
        self.count_trade_conf = 0

        self.trades_list = []
        self.market_list = []

    def send_trade_allow_request(self, trade_offer_id: str) -> dict:
        confirmations = self._get_confirmations()
        confirmation = self._select_trade_offer_confirmation(confirmations, trade_offer_id)
        return self._send_confirmation(confirmation)

    def confirm_sell_listing(self, asset_id: str) -> dict:
        confirmations = self._get_confirmations()
        confirmation = self._select_sell_listing_confirmation(confirmations, asset_id)
        return self._send_confirmation(confirmation)

    def _send_confirmation(self, confirmation: Confirmation) -> dict:
        tag = Tag.ALLOW
        params = self._create_confirmation_params(tag.value)
        params['op'] = tag.value,
        params['cid'] = confirmation.data_confid
        params['ck'] = confirmation.data_key
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        return self._session.get(self.CONF_URL + '/ajaxop', params=params, headers=headers, timeout=15).json()

    def _send_confirmation_api_key(self, confirmation: Confirmation) -> dict:
        tag = Tag.ALLOW
        params = self._create_confirmation_params(tag.value)
        params['op'] = tag.value,
        params['cid'] = confirmation.data_confid
        params['ck'] = confirmation.data_key
        headers = {
            'Cookie': self.get_steam_comm_cookie(),
            'X-Requested-With': 'XMLHttpRequest'
        }
        return self._session.get(self.CONF_URL + '/ajaxop', params=params, headers=headers, timeout=15).json()

    def get_cookies(self):
        dictri = self._session.cookies.get_dict()
        str = ''
        for key in dictri:
            str += key + '=' + dictri[key] + '; '

        return str[0: len(str) - 2]

    def _get_confirmations(self) -> List[Confirmation]:
        confirmations = []
        confirmations_page = self._fetch_confirmations_page()
        if 'conf' in confirmations_page and len(confirmations_page['conf']) > 0:
            for confirmation in confirmations_page['conf']:
                _id = confirmation['id']
                data_confid = confirmation['id']
                data_key = confirmation['nonce']
                type = confirmation['type']
                if 'creator_id' in confirmation:
                    trade_id = confirmation['creator_id']
                else:
                    trade_id = None
                if type == 3:
                    self.count_market_conf += 1
                    self.market_list.append(_id)
                elif type == 2:
                    self.count_trade_conf += 1
                    self.trades_list.append(_id)
                confirmations.append(Confirmation(f'conf{_id}', data_confid, data_key, trade_id))
        else:
            confirmations = []
        return confirmations

    def _fetch_confirmations_page(self) -> requests.Response:
        tag = Tag.CONF.value
        params = self._create_confirmation_params(tag)
        headers = {'X-Requested-With': 'com.valvesoftware.android.steam.community'}
        response = self._session.get(self.CONF_URL + '/getlist', params=params, headers=headers, timeout=15).json()
        return response

    def get_steam_comm_cookie(self):
        str = ''
        for cookie in self._session.cookies:
            if cookie.domain == 'steamcommunity.com':
                str += cookie.name + '=' + cookie.value + '; '
        return str[0: len(str) - 2]

    def _fetch_confirmations_page_api_key(self) -> dict:
        tag = Tag.CONF.value
        params = self._create_confirmation_params(tag)

        headers = {
            "Cookie": self.get_steam_comm_cookie(),
            'X-Requested-With': 'com.valvesoftware.android.steam.community'
        }
        response = self._session.get(self.CONF_URL + '/getlist', params=params, headers=headers, timeout=15).json()
        return response

    def _fetch_confirmation_details_page(self, confirmation: Confirmation) -> str:
        tag = 'details' + id
        params = self._create_confirmation_params(tag)
        response = self._session.get(self.CONF_URL + '/details/' + id, params=params, timeout=15)
        return response.json()['html']

    def _create_confirmation_params(self, tag_string: str) -> dict:
        timestamp = int(time.time())
        confirmation_key = guard.generate_confirmation_key(self._identity_secret, tag_string, timestamp)
        android_id = guard.generate_device_id(self._my_steam_id)
        return {'p': android_id,
                'a': self._my_steam_id,
                'k': confirmation_key,
                't': timestamp,
                'm': 'android',
                'tag': tag_string}

    def _select_trade_offer_confirmation(self, confirmations: List[Confirmation], trade_offer_id: str) -> Confirmation:
        for confirmation in confirmations:
            if confirmation.trade_id == trade_offer_id:
                return confirmation
        raise ConfirmationExpected

    def _select_sell_listing_confirmation(self, confirmations: List[Confirmation], asset_id: str) -> Confirmation:
        for confirmation in confirmations:
            confirmation_details_page = self._fetch_confirmation_details_page(confirmation)
            if asset_id in confirmation_details_page:
                return confirmation
        raise ConfirmationExpected

    def return_session(self):
        return self._session

    @staticmethod
    def _get_confirmation_sell_listing_id(confirmation_details_page: str) -> str:
        soup = BeautifulSoup(confirmation_details_page, 'html.parser')
        scr_raw = soup.select("script")[2].string.strip()
        scr_raw = scr_raw[scr_raw.index("'confiteminfo', ") + 16:]
        scr_raw = scr_raw[:scr_raw.index(", UserYou")].replace("\n", "")
        return json.loads(scr_raw)["id"]

    @staticmethod
    def _get_confirmation_trade_offer_id(confirmation_details_page: str) -> str:
        soup = BeautifulSoup(confirmation_details_page, 'html.parser')
        full_offer_id = soup.select('.tradeoffer')[0]['id']
        return full_offer_id.split('_')[1]
