from bots_libraries.information.logs import Logs
from bots_libraries.information.mongo import Mongo
from bots_libraries.creator.creator_steam import Steam
from bots_libraries.steampy.confirmation import ConfirmationExecutor
from bots_libraries.steampy.confirmation import Confirmation
from bots_libraries.steampy.models import GameOptions
from bots_libraries.steampy.client import SteamClient
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
import threading
import json

class TMOnline(Steam):
    def __init__(self):
        super().__init__()


    def request_ping(self):
        json_data = {
            'access_token': f"{self.steamclient.access_token}"
        }
        if 'http' in self.steamclient.proxies:
            json_data['proxy'] = self.steamclient.proxies['http']
        url = f"https://market.csgo.com/api/v2/ping-new?key=" + self.steamclient.tm_api
        try:
            response = requests.post(url, json=json_data, timeout=10)
            if response:
                response_data = response.json()
                if response_data['success'] is False and response_data['message'] != 'too early for pong':
                    Logs.log(f"{self.steamclient.username}: Ping Error: {response_data['message']}")
                    self.tm_tg_bot.send_message(self.tm_tg_id,
                                                f'TM Seller: Ping Error: {self.steamclient.username}')
        except:
            pass

    def ping(self, acc_info, time_sleep):
        while True:
            self.update_account_data_info()
            username = ''
            try:
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                username = acc_info['username']
                self.request_ping()
            except:
                Logs.log(f"Error during take session in ping for {username}")
            time.sleep(time_sleep)

    def store_ping(self, acc_info, time_sleep):
        while True:
            self.update_account_data_info()
            username = ''
            try:
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                username = acc_info['username']
                url = f'https://market.csgo.com/api/v2/go-offline?key={self.steamclient.tm_api}'
                response = requests.get(url, timeout=10)
                response_data = response.json()
                print(response_data)
                if response_data['success'] is not True:
                    Logs.log(f'Restart Store Error')
            except:
                Logs.log(f"Error in store_ping for {username}")
            time.sleep(2)
            self.request_ping()
            time.sleep(time_sleep)

    def store_items_visible(self):
        while True:
            pass






