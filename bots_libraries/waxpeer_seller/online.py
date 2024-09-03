import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam import Steam
from bots_libraries.sellpy.logs import Logs, ExitException


class WaxpeerOnline(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.ping_alert = False

    def ping(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    try:
                        url_to_ping = (f'{self.site_url}/v1/check-wss-user?'
                                       f'api=1{self.waxpeer_apikey}&'
                                       f'steamid={self.steamclient.steam_guard["steamid"]}')
                        response = requests.get(url_to_ping, timeout=15).json()
                    except:
                        response = None
                    if (response and 'success' in response and response['success'] is False
                            and 'msg' in response and response['msg'] != 'wrong api'):
                        Logs.log(f"Ping: Error to ping: {response['msg']}", self.steamclient.username)
                        if not self.ping_alert:
                            Logs.notify(self.tg_info, f"Ping: Error to ping: {response['msg']}",
                                        self.steamclient.username)
                            self.ping_alert = True
            except Exception as e:
                Logs.notify_except(self.tg_info, f'Ping Global Error: {e}', self.steamclient.username)
            time.sleep(self.ping_global_time)
