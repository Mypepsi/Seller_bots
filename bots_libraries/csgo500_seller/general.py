import jwt
import time
import random
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam


class CSGO500General(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    def database_csgo500(self):  # Global Function (class_for_account_functions)
        Logs.log(f"Database CSGO500: thread are running", '')
        while True:
            try:
                current_timestamp = int(time.time())
                try:
                    csgo500_doc = self.database_csgo500_collection.find_one()
                except:
                    csgo500_doc = None
                if csgo500_doc:
                    last_update_time = int(csgo500_doc.get("Time", 0))
                else:
                    last_update_time = 0

                difference_to_update = current_timestamp - last_update_time
                if difference_to_update > self.db_csgo500_validity_time:
                    try:
                        another_apis_list = self.search_in_merges_by_username(
                            self.steamclient.username)['csgo500 parse']
                    except:
                        another_apis_list = None
                    if another_apis_list:
                        another_api = random.choice(another_apis_list)
                        another_jwt_api_key = jwt.encode(
                            {'userId': another_api['user_id']},
                            another_api['apikey'],
                            algorithm="HS256"
                        )
                        another_csgo500_jwt_apikey = {'x-500-auth': another_jwt_api_key}
                        payload = {"pagination": {"referenceId": "",
                                                  "referenceFilterValue": 0,
                                                  "limit": 500,
                                                  "direction": "next"},
                                   "filters": {"appId": 730}}
                        counter = 0
                        data = {}
                        while counter < 1:
                            try:
                                search_url = f'{self.site_url}/api/v1/market/shop'
                                search_response = requests.post(search_url, headers=another_csgo500_jwt_apikey,
                                                                json=payload, timeout=15).json()
                                for item in search_response['data']['listings']:
                                    entry = {'site_item_id': item['id'], 'price': item['value']}
                                    if item['name'] in data:
                                        data[item['name']].append(entry)
                                    else:
                                        data[item['name']] = [entry]
                                if search_response.get('success') and len(search_response['data']['listings']) < 450:
                                    break
                                payload['pagination']["referenceId"] = search_response['data']['listings'][-1]['id']
                                payload['pagination']["referenceFilterValue"] = search_response[
                                    'data']['listings'][-1]['value']
                            except:
                                counter += 1

                            time.sleep(1)
                        csgo500_dict = {"Time": current_timestamp,
                                        "DataBaseCSGO500": data}
                        try:
                            self.database_csgo500_collection.replace_one({}, csgo500_dict, upsert=True)
                            Logs.log(f"Database CSGO500: DB Settings has been updated in MongoDB", '')

                        except Exception as e:
                            Logs.notify_except(self.tg_info,
                                               f"Database CSGO500: MongoDB critical request failed: {e}",
                                               '')
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Database CSGO500 Global Error: {e}", '')
            time.sleep(self.db_csgo500_global_time)
