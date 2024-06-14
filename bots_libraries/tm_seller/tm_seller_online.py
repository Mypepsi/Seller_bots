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


    def work_with_steam_create_thread(self, function, time_sleep):

        for acc in self.content_accs_parsed_list:
            self.username = acc['username']
            steam_session = acc['steam session']
            self.take_session(steam_session)
            thread = threading.Thread(target=function)
            thread.start()
            thread.join()
        time.sleep(time_sleep)


    def online(self):
        tm_apikey = self.content_accs_dict[self.username]['tm apikey']
        print(self.username + '  ' + tm_apikey + '  ' + self.steamclient.access_token)
        url = f"https://market.csgo.com/api/v2/ping-new?key=" + tm_apikey
        response = requests.post(url, json={
                'access_token': self.steamclient.access_token,
                'proxy': self.steamclient.proxies['http']
            })
        if response:
            try:
                response_data = response.json()
                print(response_data)
                if "message" in response_data and "You cant trade until" in response_data["message"]:
                    Logs.log(f'ответ {response_data }')
            except Exception:
                Logs.log(f'ошибка json')
        else:
            try:
                response = response.json()
                if "message" in response and "You cant trade until" in response["message"]:
                    Logs.log(f"TM Seller: Store OFFLINE: haven`t transferred too many items")
            except Exception:
                pass
