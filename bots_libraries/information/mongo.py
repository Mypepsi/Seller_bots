from pymongo import MongoClient
from bots_libraries.information.logs import Logs
import telebot


class Mongo:
    def __init__(self):
        self.client = MongoClient("mongodb://127.0.0.1:27017")
        self.database = self.get_database('Seller_DataBases')
        self.database_price_collection = self.get_collection(self.database, 'database_prices')
        self.database_settings_collection = self.get_collection(self.database, 'database_settings')

        self.settings = self.get_database('Seller_Settings')
        self.creator_settings_collection = self.get_collection(self.settings, 'creator_settings')
        self.tm_settings_collection = self.get_collection(self.settings, 'tm_seller_settings')

        self.accs = self.get_database('Seller_Accounts')
        self.acc_settings_collection = self.get_collection(self.accs, 'account_settings')
        self.acc_data_collection = self.get_collection(self.accs, 'account_data')
        self.acc_for_parsing_collection = self.get_collection(self.accs, 'account_for_parsing')

        self.update_mongo_info()

        self.content_settings_creator = self.get_from_mongo_doc(self.creator_settings_collection)
        self.content_settings_tm = self.get_from_mongo_doc(self.tm_settings_collection)

        self.content_acc_list = self.get_from_mongo_doc_list(self.acc_settings_collection)
        self.content_acc_dict = self.get_from_mongo_doc_dict(self.acc_settings_collection,
                                                             'username')
        self.content_acc_for_parsing_list = self.get_from_mongo_doc_list(self.acc_for_parsing_collection)
        self.content_matches = self.create_merge_acc_for_parsing_and_acc_sittings()



        # region information from creator settings collection
        self.creator_settings_general = self.get_keys(self.content_settings_creator, 'general')
        self.creator_tg_token = self.get_keys(self.creator_settings_general, 'tg token')
        self.creator_tg_id = self.get_keys(self.creator_settings_general, 'tg id')
        self.creator_sleep_before_start = self.get_keys(self.creator_settings_general, 'waiting start time')
        self.creator_sleep_between_threads = self.get_keys(self.creator_settings_general, 'thread start time')
        if self.creator_tg_token:
            self.creator_tg_bot = telebot.TeleBot(self.creator_tg_token)

        self.creator_settings_database = self.get_keys(self.content_settings_creator, 'database')
        self.creator_db_prices_url = self.get_keys(self.creator_settings_database, 'db prices url')
        self.creator_db_settings_url = self.get_keys(self.creator_settings_database, 'db settings url')
        self.creator_db_price_sleep_time = self.get_keys(self.creator_settings_database, 'db prices validity time')
        self.creator_db_settings_sleep_time = self.get_keys(self.creator_settings_database, 'db settings validity time')
        self.creator_db_prices_global_time = self.get_keys(self.creator_settings_database, 'db prices global time')
        self.creator_db_settings_global_time = self.get_keys(self.creator_settings_database, 'db settings global time')

        self.creator_settings_steam = self.get_keys(self.content_settings_creator, 'steam')
        self.creator_authorization_time_sleep = self.get_keys(self.creator_settings_steam, 'steam session validity time')
        self.creator_steam_api_key_global_sleep = self.get_keys(self.creator_settings_steam, 'steam apikey global time')
        self.creator_steam_inventory_global_sleep = self.get_keys(self.creator_settings_steam, 'steam inventory global time')
        self.creator_authorization_global_sleep = self.get_keys(self.creator_settings_steam, 'steam session global time')
        self.creator_hashname_difference_time = self.get_keys(self.creator_settings_steam, 'steam inventory hashname validity time')
        self.creator_proxy_check_url = self.get_keys(self.creator_settings_steam, 'proxy url')
        self.creator_proxy_global_sleep = self.get_keys(self.creator_settings_steam, 'proxy global time')
        self.creator_access_token_global_sleep = self.get_keys(self.creator_settings_steam, 'steam access token global time')
        self.creator_access_token_start_sleep = self.get_keys(self.creator_settings_steam, 'steam access token waiting start time')

        self.creator_settings_restart = self.get_keys(self.content_settings_creator, 'restart')
        self.creator_restart_time_sleep = self.get_keys(self.creator_settings_restart, 'restart server validity time')
        self.creator_restart_server_global_sleep = self.get_keys(self.creator_settings_restart, 'restart server global time')
        self.creator_restart_bots_global_sleep = self.get_keys(self.creator_settings_restart, 'restart bots global time')
        self.creator_restart_info_bots = self.get_keys(self.creator_settings_restart, 'restart bots name')  # list of dict


        # endregion

        # region information from tm settings collection
        self.tm_settings_general = self.get_keys(self.content_settings_tm, 'general')
        self.tm_sleep_before_start = self.get_keys(self.tm_settings_general, 'waiting start time')
        self.tm_sleep_between_threads = self.get_keys(self.tm_settings_general, 'thread start time')
        self.tm_thread_function_sleep = self.get_keys(self.tm_settings_general, 'thread function time')
        self.tm_tg_id = self.get_keys(self.tm_settings_general, 'tg id')
        self.tm_tg_token = self.get_keys(self.tm_settings_general, 'tg token')
        if self.tm_tg_token:
            self.tm_tg_bot = telebot.TeleBot(self.tm_tg_token)
        self.tm_history_tg_id = self.get_keys(self.tm_settings_general, 'history tg id')
        self.tm_history_tg_token = self.get_keys(self.tm_settings_general, 'history tg token')
        if self.tm_history_tg_token:
            self.tm_history_tg_bot = telebot.TeleBot(self.tm_history_tg_token)

        self.tm_url = self.get_keys(self.tm_settings_general, 'tm url')

        self.tm_settings_online = self.get_keys(self.content_settings_tm, 'online')
        self.tm_ping = self.get_keys(self.tm_settings_online, 'tm ping')
        self.tm_store_ping = self.get_keys(self.tm_settings_online, 'tm store ping')

        self.tm_settings_restart = self.get_keys(self.content_settings_tm, 'restart')
        self.tm_restart_time_sleep = self.get_keys(self.tm_settings_restart, 'restart server validity time')
        self.tm_restart_server_global_sleep = self.get_keys(self.tm_settings_restart, 'restart server global time')
        self.tm_restart_bots_global_sleep = self.get_keys(self.tm_settings_restart, 'restart bots global time')
        self.tm_restart_info_bots = self.get_keys(self.tm_settings_restart, 'restart bots name')  # list of dict
        # endregion

    def update_mongo_info(self):
        try:
            self.content_acc_data_list = self.get_from_mongo_doc_list(self.acc_data_collection)
            self.content_acc_data_dict = self.get_from_mongo_doc_dict(self.acc_data_collection,
                                                                         'username')
        except Exception as e:
            Logs.log(f'Error while updating data from mongo: {e}')

    def create_merge_acc_for_parsing_and_acc_sittings(self):
        result = []
        try:
            if len(self.content_acc_for_parsing_list) < len(self.content_acc_list):
                raise ValueError
            unique_iterator = iter(self.content_acc_for_parsing_list)
            for acc in self.content_acc_list:
                unique_acc = next(unique_iterator)
                result.append([acc, unique_acc])
            return result

        except ValueError:
            Logs.log("Not enough parsing objects for all accounts in accounts for parsing")
            return result
        except:
            Logs.log("Error during taking info for parsing")
            return result


    def get_database(self, db_name):
        try:
            return self.client[db_name]
        except Exception as e:
            Logs.log(f"Error during receiving database {db_name}: {e}")
            return None

    def get_collection(self, database, collection_name):
        if database is None:
            return None
        try:
            return database[collection_name]
        except Exception as e:
            Logs.log(f"Error during receiving collection {collection_name}: {e}")
            return None

    @staticmethod
    def get_keys(dictionary, key):
        try:
            if key in dictionary:
                dictionary = dictionary[key]
            else:
                Logs.log(f"Key '{key}' not found in {dictionary}")
            return dictionary
        # except TypeError:
        #     Logs.log(f"Error during receiving {key}: it does not exist in MongoDB")
        #     return None
        except Exception as e:
            # Logs.log(f"Error during receiving key: {key} in {dictionary}: {e}")
            return None


    @staticmethod
    def get_from_mongo_doc(collection):
        results = collection.find({})
        for result in results:
            return result

    @staticmethod
    def get_from_mongo_doc_list(collection):
        results = collection.find({})
        results_list = []
        for result in results:
            results_list.append(result)
        return results_list

    @staticmethod
    def get_from_mongo_doc_dict(collection, key_name):
        results = collection.find({})
        results_dict = {}
        for doc in results:
            account_name = doc.get(key_name)
            if account_name:
                results_dict[account_name] = doc
        return results_dict







