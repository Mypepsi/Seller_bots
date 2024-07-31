import re
import json
import time
import pickle
import string
import random
import requests
import traceback
from lxml import html
from bots_libraries.sellpy.logs import Logs
from bots_libraries.steampy.client import SteamClient
from bots_libraries.steampy.models import GameOptions
from bots_libraries.steampy.confirmation import Confirmation
from bots_libraries.sellpy.thread_manager import ThreadManager
from bots_libraries.steampy.confirmation import ConfirmationExecutor


class CreatorGeneral(ThreadManager):
    def __init__(self):
        super().__init__()
        self.questionable_proxies = {}

    def proxy_checker(self, time_sleep):
        Logs.log(f'Proxy Checker: thread are running', '')
        while True:
            try:
                self.update_account_data_info()
                self.proxy_for_check = []
                for acc in self.content_acc_data_list:
                    try:
                        self.take_session(acc)
                        if self.steamclient.proxies:
                            self.proxy_for_check.append(self.steamclient.proxies)
                    except:
                        pass
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
                        response = requests.get(self.creator_proxy_check_url, proxies=proxy, timeout=15)
                        if response.status_code == 200:
                            try:
                                del self.questionable_proxies[proxy_ip]
                            except KeyError:
                                pass
                    except:
                        if proxy_ip in self.questionable_proxies:
                            self.questionable_proxies[proxy_ip] += 1
                            if self.questionable_proxies[proxy_ip] == 3:
                                Logs.notify(self.creator_tg_info, f'Proxy Checker: Multiple errors for {proxy_ip}', '')
                        else:
                            self.questionable_proxies[proxy_ip] = 1
                        Logs.log(f'Proxy Error:', proxy_ip)
                    time.sleep(10)
            except Exception as e:
                Logs.notify_except(self.creator_tg_info, f'Proxy Checker Global Error: {e}', '')
            time.sleep(time_sleep)
