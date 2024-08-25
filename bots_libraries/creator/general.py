import time
import requests
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.steam import Steam


class CreatorGeneral(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)
        self.questionable_proxies = {}
        self.mongo_tg_alert = False

    def proxy(self):
        Logs.log(f"Proxy: thread are running", '')
        while True:
            try:
                self.update_account_data_info()
                proxy_list = []
                for acc in self.content_acc_data_list:
                    if self.take_session(acc) and self.steamclient.proxies:
                        proxy_list.append(self.steamclient.proxies)
                unique_proxy_list = []
                for proxy in proxy_list:
                    if proxy not in unique_proxy_list:
                        unique_proxy_list.append(proxy)
                proxy_for_check = unique_proxy_list

                for proxy in proxy_for_check:
                    try:
                        proxy_ip = proxy['http'].split('://')[1].split('@')[1].split(':')[0]
                    except:
                        proxy_ip = proxy
                    try:
                        response = requests.get(self.proxy_url, proxies=proxy, timeout=15)
                        if response.status_code == 200:
                            try:
                                del self.questionable_proxies[proxy_ip]
                            except KeyError:
                                pass
                        else:
                            raise ExitException
                    except:
                        Logs.log(f"Proxy: Proxy Error {proxy_ip}", '')
                        if proxy_ip in self.questionable_proxies:
                            self.questionable_proxies[proxy_ip] += 1
                            if self.questionable_proxies[proxy_ip] == 3:
                                Logs.notify(self.tg_info, f"Proxy: Multiple errors for {proxy_ip}", '')
                        else:
                            self.questionable_proxies[proxy_ip] = 1
                    time.sleep(10)
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Proxy Global Error: {e}", '')
            time.sleep(self.proxy_global_time)

    def mongodb(self):
        Logs.log(f"MongoDB: thread are running", '')
        while True:
            if not self.mongo_tg_alert:
                try:
                    response = self.client.admin.command('ping')
                    if response['ok'] != 1:
                        raise ExitException
                except Exception as e:
                    self.mongo_tg_alert = True
                    Logs.notify_except(self.tg_info, f"MongoDB: MongoDB critical request failed: {e}", '')
            time.sleep(self.mongodb_global_time)
