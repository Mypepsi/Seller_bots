import time
import requests
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.thread_manager import ThreadManager


class CreatorGeneral(ThreadManager):
    def __init__(self, name):
        super().__init__(name)
        self.questionable_proxies = {}
        self.mongo_tg_alert = False

    def proxy_checker(self, tg_info, global_time):
        Logs.log(f"Proxy Checker: thread are running", '')
        while True:
            try:
                self.update_account_data_info()
                proxy_list = []
                for acc in self.content_acc_data_list:
                    active_session = self.take_session(acc, tg_info)
                    if active_session and self.steamclient.proxies:
                        proxy_list.append(self.steamclient.proxies)
                unique_proxy_list = []
                for proxy in proxy_list:
                    if proxy not in unique_proxy_list and proxy is not None:
                        unique_proxy_list.append(proxy)
                proxy_for_check = unique_proxy_list

                for proxy in proxy_for_check:
                    try:
                        proxy_ip = proxy['http'].split('://')[1].split('@')[1].split(':')[0]
                    except:
                        proxy_ip = proxy
                    try:
                        response = requests.get(self.creator_proxy_url, proxies=proxy, timeout=15)
                        if response.status_code == 200:
                            try:
                                del self.questionable_proxies[proxy_ip]
                            except KeyError:
                                pass
                    except:
                        Logs.log(f"Proxy Checker: Proxy Error {proxy_ip}", '')
                        if proxy_ip in self.questionable_proxies:
                            self.questionable_proxies[proxy_ip] += 1
                            if self.questionable_proxies[proxy_ip] == 3:
                                Logs.notify(tg_info, f"Proxy Checker: Multiple errors for {proxy_ip}", '')
                        else:
                            self.questionable_proxies[proxy_ip] = 1
                    time.sleep(10)
            except Exception as e:
                Logs.notify_except(tg_info, f"Proxy Checker Global Error: {e}", '')
            time.sleep(global_time)

    def mongodb_checker(self, tg_info, global_time):
        Logs.log(f"MongoDB Checker: thread are running", '')
        while True:
            try:
                response = self.client.admin.command('ping')
                if response.get('ok') != 1 and not self.mongo_tg_alert:
                    self.mongo_tg_alert = True
                    raise ExitException
            except Exception as e:
                Logs.notify_except(tg_info, f"MongoDB Checker: MongoDB did not answered: {e}", '')
            time.sleep(global_time)