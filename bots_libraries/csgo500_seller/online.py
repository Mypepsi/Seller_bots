import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam import Steam
from bots_libraries.sellpy.logs import Logs, ExitException


class CSGO500Online(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.ping_alert = False

    def ping(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url_to_ping = 'https://tradingapi.500.casino/api/v1/market/ping'
                        params = {"version": 2}
                        print(self.csgo500_jwt_apikey)
                        response = requests.post(
                            url_to_ping, headers=self.csgo500_jwt_apikey, data=params, timeout=15).json()
                        print(response)
                    except:
                        response = None
                    if (response and 'success' in response and response['success'] is False
                            and 'message' in response and response['message'] != 'Ping too soon.'):
                        Logs.log(f"Ping: Error to ping: {response['message']}", self.steamclient.username)
                        if not self.ping_alert:
                            Logs.notify(self.tg_info, f"Ping: Error to ping: {response['message']}",
                                        self.steamclient.username)
                            self.ping_alert = True
            except Exception as e:
                Logs.notify_except(self.tg_info, f'Ping Global Error: {e}', self.steamclient.username)
            time.sleep(self.ping_global_time)

