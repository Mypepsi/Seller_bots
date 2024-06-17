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

        response = requests.post(url, json=json_data, timeout=10)
        if response:
            try:
                response_data = response.json()
                print(response_data)
                if "message" in response_data and "You cant trade until" in response_data[
                    "message"]:  # прим. далі не опрацьовано
                    Logs.log(f'ответ {response_data}')
            except Exception:
                Logs.log(f'{self.steamclient.username}: Ping Json-Error')
        else:
            try:
                response = response.json()
                if "message" in response and "You cant trade until" in response["message"]:
                    Logs.log(f"TM Seller: Store OFFLINE: haven`t transferred too many items")
                    self.tm_tg_bot.send_message(self.tm_tg_id,
                                                (f'TM Seller: Store OFFLINE: {self.steamclient.username}'))

            except Exception:
                Logs.log(f'{self.steamclient.username}: Ping Error')
                self.tm_tg_bot.send_message(self.tm_tg_id, (f'TM Seller: Ping Error: {self.steamclient.username}'))

    def ping(self, acc_info, time_sleep):
        while True:
            self.update_mongo_info()
            try:
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                self.request_ping()
            except:
                if acc_info['username']:
                    Logs.log(f"Error during take session in ping for {acc_info['username']}")
                else:
                    Logs.log(f'Error during take session in ping')
            time.sleep(time_sleep)

    def store_ping(self, acc_info, time_sleep):
        while True:
            try:
                self.update_mongo_info()
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                url = f'https://market.csgo.com/api/v2/go-offline?key={self.steamclient.tm_api}'
                response = requests.get(url, timeout=10)
                if response['success']:
                    Logs.log(f'Sales Stopped')
                else:
                    Logs.log(f'Sales doesn`t Stopped')
            except:
                if acc_info['username']:
                    Logs.log(f"Error in store_ping for {acc_info['username']}")
                else:
                    Logs.log(f'Error store_ping')
            time.sleep(2)
            self.request_ping()
            #прим. нижче вставити функцію онлайн?
            # json_data = {
            #     'access_token': f"{self.steamclient.access_token}"
            # }
            # if 'http' in self.steamclient.proxies:
            #     json_data['proxy'] = self.steamclient.proxies['http']
            # url = f"https://market.csgo.com/api/v2/ping-new?key=" + self.steamclient.tm_api
            # response = requests.post(url, json=json_data, timeout=10)
            # if response:
            #     try:
            #         response_data = response.json()
            #         print(response_data)
            #         if "message" in response_data and "You cant trade until" in response_data["message"]:  # прим. далі не опрацьовано
            #             Logs.log(f'ответ {response_data}')
            #     except Exception:
            #         Logs.log(f'{self.steamclient.username}: Ping Json-Error')
            # else:
            #     try:
            #         response = response.json()
            #         if "message" in response and "You cant trade until" in response["message"]:
            #             Logs.log(f"TM Seller: Store OFFLINE: haven`t transferred too many items")
            #             self.tm_tg_bot.send_message(self.tm_tg_id,
            #                                         (f'TM Seller: Store OFFLINE: {self.steamclient.username}'))
            #
            #     except Exception:
            #         Logs.log(f'{self.steamclient.username}: Ping Error')
            time.sleep(time_sleep)

    def store_items_visible(self):
        pass
