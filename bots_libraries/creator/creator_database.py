from pymongo.errors import ServerSelectionTimeoutError
from bots_libraries.base_info.logs import Logs
from bots_libraries.base_info.mongo import Mongo
import time
import requests


class DataBase(Mongo):
    def __init__(self):
        super().__init__()

    def refresh_db_thread(self):
        while True:
            current_timestamp = int(time.time())
            try:
                db_doc = self.database_prices_collection.find_one()
                if db_doc:
                    last_update_time = int(db_doc.get("Time", 0))
                else:
                    db_doc = {
                        "Time": 0,
                        "DataBasePrices": []
                    }
                    self.database_prices_collection.insert_one(db_doc)
                    last_update_time = db_doc["Time"]

                difference_to_update = current_timestamp - last_update_time
                if difference_to_update > self.creator_db_price_sleep_time:
                    try:
                        db_rs = requests.get(self.creator_db_prices_url, timeout=20)
                        if db_rs.status_code == 200:
                            db = db_rs.json()
                            if db:
                                Logs.log("DataBasePrices: Database is uploaded")
                                try:
                                    currency_data = requests.get(self.creator_db_settings_url, timeout=20)
                                    if currency_data.status_code == 200:
                                        currency_rs = currency_data.json()
                                        if currency_rs:
                                            Logs.log("DataBasePrices: Settings is uploaded")
                                            db_seller_max_price_list = currency_rs['Creator_DataBaseMaxPrice']

                                            db_list = []

                                            for hashname in db.keys():
                                                data_dict = {}

                                                max_round_currency_price = 0

                                                service_max_price = None

                                                buff_currency_rate = currency_rs['Creator_DataBaseRate']['DataBaseRate_buff']

                                                try:
                                                    buff_full_price = round(db[hashname]['buff']['price'] / buff_currency_rate, 2)
                                                except KeyError:
                                                    buff_full_price = 0
                                                try:
                                                    steam_full_price = round(db[hashname]['steam']['price'], 2)
                                                except KeyError:
                                                    steam_full_price = 0

                                                data_dict[hashname] = {
                                                    "buff_full_price": buff_full_price,
                                                    "steam_full_price": steam_full_price,
                                                    "max_price": 0,
                                                    "service_max_price": None
                                                }

                                                for item in db_seller_max_price_list:
                                                    db_min_sales = item['min sales']
                                                    db_validity_time = item['validity time']

                                                    price_service = item['price service']
                                                    price_type_update = item['price type'] + 'Update'

                                                    key_name = price_service + '_max_price'
                                                    key_value = 0

                                                    if key_name not in data_dict[hashname]:
                                                        data_dict[hashname][key_name] = key_value
                                                    else:
                                                        key_value = data_dict[hashname][key_name]

                                                    currency_rate_name = 'DataBaseRate_' + price_service
                                                    currency_rate = currency_rs['Creator_DataBaseRate'][currency_rate_name]
                                                    try:
                                                        sales_for_week = db[hashname][price_service]['salesForWeek']
                                                    except KeyError:
                                                        sales_for_week = 0
                                                    if sales_for_week > db_min_sales:
                                                        current_timestamp = int(time.time())
                                                        try:
                                                            price_from_db = int(db[hashname][price_service]
                                                                                [price_type_update]) / 1000  # round up milliseconds
                                                        except KeyError:
                                                            price_from_db = 0
                                                        difference = int(current_timestamp - price_from_db)
                                                        if difference < db_validity_time:
                                                            rate_type = item['rate type']
                                                            if rate_type == 0 and currency_rate > 0:
                                                                currency_price = db[hashname][price_service][
                                                                                     item['price type']] * currency_rate
                                                            elif rate_type == 1 and currency_rate > 0:
                                                                currency_price = db[hashname][price_service][
                                                                                     item['price type']] / currency_rate
                                                            else:
                                                                currency_price = 0

                                                            commission_type = item['commission type']
                                                            commission = item['commission']
                                                            if commission_type == 0 and commission > 0:
                                                                currency_price_with_commission = currency_price * commission
                                                            elif commission_type == 1 and commission > 0:
                                                                currency_price_with_commission = commission_type / commission
                                                            else:
                                                                currency_price_with_commission = 0

                                                            round_currency_price = round(currency_price_with_commission, 2)

                                                            if round_currency_price > key_value:
                                                                data_dict[hashname].update({key_name: round_currency_price})

                                                            if round_currency_price > max_round_currency_price:
                                                                max_round_currency_price = round_currency_price
                                                                service_max_price = price_service

                                                            data_dict[hashname].update({
                                                                "max_price": max_round_currency_price,
                                                                "service_max_price": service_max_price
                                                            })
                                                db_list.append(data_dict)

                                            if len(db_list) != 0:
                                                current_timestamp = int(time.time())
                                                db_dict = {"Time": current_timestamp,
                                                           "DataBasePrices": db_list}

                                                self.database_prices_collection.replace_one({}, db_dict, upsert=True)
                                                Logs.log(f"DataBasePrices: Database Prices has been updated in MongoDB")
                                        else:
                                            Logs.log("Error in keys refresh_db_thread-1")
                                    else:
                                        Logs.log("Error in status code refresh_db_thread-2")
                                except:
                                    Logs.log(f"Error in refresh_db_thread-3")
                        else:
                            Logs.log("Error in status code refresh_db_thread-4")
                    except:
                        Logs.log(f"Error in refresh_db_thread-5")
            except:
                Logs.log(f"Error in refresh_db_thread-6")
            time.sleep(self.creator_db_prices_global_time)

    def refresh_settings_thread(self):
        while True:
            current_timestamp = int(time.time())
            try:
                settings_doc = self.database_settings_collection.find_one()
                if settings_doc:
                    last_update_time = int(settings_doc.get("Time", 0))
                else:
                    settings_doc = {
                        "Time": 0,
                        "DataBaseSettings": []
                    }
                    self.database_settings_collection.insert_one(settings_doc)
                    last_update_time = settings_doc["Time"]

                difference_to_update = current_timestamp - last_update_time
                if difference_to_update > self.creator_db_settings_sleep_time:
                    try:
                        currency_data = requests.get(self.creator_db_settings_url, timeout=20)
                        if currency_data.status_code == 200:
                            currency_rs = currency_data.json()
                            if currency_rs:
                                Logs.log("DataBaseSettings: Settings is uploaded")
                                current_timestamp = int(time.time())
                                settings_dict = {"Time": current_timestamp,
                                                 "DataBaseSettings": currency_rs}
                                self.database_settings_collection.replace_one({}, settings_dict, upsert=True)
                                Logs.log("DataBaseSettings: Database Settings has been updated in MongoDB")
                            else:
                                Logs.log("Error in keys refresh_settings_thread-1")
                        else:
                            Logs.log("Error in status code refresh_settings_thread-2")
                    except requests.exceptions.RequestException:
                        Logs.log(f"Error in refresh_settings_thread-3")
            except ServerSelectionTimeoutError:
                Logs.log(f"Error in refresh_settings_thread-4")
            time.sleep(self.creator_db_settings_global_time)
