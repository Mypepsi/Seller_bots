import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam import Steam
from bots_libraries.sellpy.logs import Logs, ExitException


class BuffOnline(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.ping_alert = False

    def ping(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    response = self.request_to_ping(0)
                    if response and "error" in response:
                        Logs.log(f"Ping: Error to ping: {response['error']}", self.steamclient.username)
                        if not self.ping_alert:
                            Logs.notify(self.tg_info, f"Ping: Error to ping: {response['error']}",
                                        self.steamclient.username)
                            self.ping_alert = True
            except Exception as e:
                Logs.notify_except(self.tg_info, f'Ping Global Error: {e}', self.steamclient.username)
            time.sleep(self.ping_global_time)

    def request_to_ping(self, status, timeout=15):
        try:
            url_to_ping = f'{self.site_url}/api/market/user_store/change_state'
            headers = {
                "Host": "buff.163.com",
                "Origin": "https://buff.163.com",
                "Referer": "https://buff.163.com/market/sell_order/on_sale?game=csgo&mode=2,5",
                "X-CSRFToken": self.buff_cookie.get("csrf_token"),
                'User-Agent': self.steamclient.user_agent
            }
            json_data = {
                "state": f"{status}",
                "auto_offline": "0",
                "auto_offline_hour": "",
                "auto_offline_minute": ""
            }
            response = requests.post(url_to_ping, json=json_data, headers=headers, cookies=self.buff_cookie,
                                     timeout=timeout).json()
            return response
        except:
            return None

    def restart_store(self):  # Global Function (class_for_account_functions)
        while True:
            try:
                if self.active_session:
                    self.request_to_ping(1)
                    time.sleep(1)
                    self.request_to_ping(0)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Restart Store Global Error: {e}", self.steamclient.username)
            time.sleep(self.restart_store_global_time)
