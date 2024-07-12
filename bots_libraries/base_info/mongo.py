from pymongo import MongoClient
from bots_libraries.base_info.logs import Logs
import telebot
import itertools


class Mongo:
    def __init__(self):

        self.client = MongoClient("mongodb://127.0.0.1:27017")
        # region information from MongoDB

        self.database = self.get_database('Seller_DataBases')
        self.database_prices_collection = self.get_collection(self.database, 'database_prices')
        self.database_settings_collection = self.get_collection(self.database, 'database_settings')
        self.content_database_prices = self.get_first_doc_from_mongo_collection(self.database_prices_collection)
        self.content_database_settings = self.get_first_doc_from_mongo_collection(self.database_settings_collection)

        self.settings = self.get_database('Seller_Settings')
        self.creator_settings_collection = self.get_collection(self.settings, 'creator_settings')
        self.content_settings_creator = self.get_first_doc_from_mongo_collection(self.creator_settings_collection)

        self.tm_settings_collection = self.get_collection(self.settings, 'tm_seller_settings')
        self.content_settings_tm = self.get_first_doc_from_mongo_collection(self.tm_settings_collection)


        self.history = self.get_database('Seller_History')


        self.accs = self.get_database('Seller_Accounts')
        self.acc_settings_collection = self.get_collection(self.accs, 'account_settings')
        self.content_acc_list = self.get_all_docs_from_mongo_collection(self.acc_settings_collection)
        self.content_acc_dict = self.get_dict_from_collection_list(self.content_acc_list, 'username')

        self.acc_data_collection = self.get_collection(self.accs, 'account_data')
        self.content_acc_data_list = self.get_all_docs_from_mongo_collection(self.acc_data_collection)
        self.content_acc_data_dict = self.get_dict_from_collection_list(self.content_acc_data_list,
                                                                        'username')

        self.acc_for_parsing_collection = self.get_collection(self.accs, 'account_for_parsing')
        self.content_acc_for_parsing_list = self.get_all_docs_from_mongo_collection(self.acc_for_parsing_collection)

        self.content_merges = self.create_merge_acc_for_parsing_and_acc_sittings()
        # endregion`

        # region information from creator settings collection
        self.creator_settings_general = self.get_key(self.content_settings_creator, 'general')
        self.creator_tg_token = self.get_key(self.creator_settings_general, 'tg token')
        self.creator_tg_id = self.get_key(self.creator_settings_general, 'tg id')
        self.creator_sleep_before_start = self.get_key(self.creator_settings_general, 'waiting start time')
        self.creator_sleep_between_threads = self.get_key(self.creator_settings_general, 'thread start time')
        if self.creator_tg_token:
            self.creator_tg_bot = telebot.TeleBot(self.creator_tg_token)

        self.creator_settings_database = self.get_key(self.content_settings_creator, 'database')
        self.creator_db_prices_url = self.get_key(self.creator_settings_database, 'db prices url')
        self.creator_db_settings_url = self.get_key(self.creator_settings_database, 'db settings url')
        self.creator_db_price_sleep_time = self.get_key(self.creator_settings_database, 'db prices validity time')
        self.creator_db_settings_sleep_time = self.get_key(self.creator_settings_database, 'db settings validity time')
        self.creator_db_prices_global_time = self.get_key(self.creator_settings_database, 'db prices global time')
        self.creator_db_settings_global_time = self.get_key(self.creator_settings_database, 'db settings global time')

        self.creator_settings_steam = self.get_key(self.content_settings_creator, 'steam')
        self.creator_authorization_time_sleep = self.get_key(self.creator_settings_steam, 'steam session validity time')
        self.creator_steam_api_key_global_sleep = self.get_key(self.creator_settings_steam, 'steam apikey global time')
        self.creator_steam_inventory_global_sleep = self.get_key(self.creator_settings_steam, 'steam inventory global time')
        self.creator_authorization_global_sleep = self.get_key(self.creator_settings_steam, 'steam session global time')
        self.creator_hashname_difference_time = self.get_key(self.creator_settings_steam, 'steam inventory hashname validity time')
        self.creator_access_token_global_sleep = self.get_key(self.creator_settings_steam, 'steam access token global time')

        self.creator_settings_proxy = self.get_key(self.content_settings_creator, 'proxy')
        self.creator_proxy_check_url = self.get_key(self.creator_settings_proxy, 'proxy url')
        self.creator_proxy_global_sleep = self.get_key(self.creator_settings_proxy, 'proxy global time')

        self.creator_settings_restart = self.get_key(self.content_settings_creator, 'restart')
        self.creator_restart_time_sleep = self.get_key(self.creator_settings_restart, 'restart server validity time')
        self.creator_restart_server_global_sleep = self.get_key(self.creator_settings_restart, 'restart server global time')
        self.creator_restart_bots_global_sleep = self.get_key(self.creator_settings_restart, 'restart bots global time')
        self.creator_restart_info_bots = self.get_key(self.creator_settings_restart, 'restart bots name')  # list of dict

        # endregion

        # region information from tm settings collection
        self.tm_settings_general = self.get_key(self.content_settings_tm, 'general')
        self.tm_sleep_before_start = self.get_key(self.tm_settings_general, 'waiting start time')
        self.tm_sleep_between_threads = self.get_key(self.tm_settings_general, 'thread start time')
        self.tm_thread_function_sleep = self.get_key(self.tm_settings_general, 'thread function time')
        self.tm_tg_id = self.get_key(self.tm_settings_general, 'tg id')
        self.tm_tg_token = self.get_key(self.tm_settings_general, 'tg token')
        if self.tm_tg_token:
            self.tm_tg_bot = telebot.TeleBot(self.tm_tg_token)
        self.tm_url = self.get_key(self.tm_settings_general, 'site url')
        self.tm_transfer_global_sleep = self.get_key(self.tm_settings_general, 'money transfer global time')
        self.tm_api_key_checker_global_sleep = self.get_key(self.tm_settings_general, 'site apikey global time')

        self.tm_settings_online = self.get_key(self.content_settings_tm, 'online')
        self.tm_ping_global_sleep = self.get_key(self.tm_settings_online, 'online ping global time')
        self.tm_visible_store_num_of_items = self.get_key(self.tm_settings_online, 'visible store max number of inv items')
        self.tm_visible_store_global_sleep = self.get_key(self.tm_settings_online, 'visible store global time')


        self.tm_settings_restart = self.get_key(self.content_settings_tm, 'restart')
        self.tm_restart_time_sleep = self.get_key(self.tm_settings_restart, 'restart server validity time')
        self.tm_restart_server_global_sleep = self.get_key(self.tm_settings_restart, 'restart server global time')
        self.tm_restart_bots_global_sleep = self.get_key(self.tm_settings_restart, 'restart bots global time')
        self.tm_restart_info_bots = self.get_key(self.tm_settings_restart, 'restart bots name')  # list of dict
        self.tm_restart_store_global_sleep = self.get_key(self.tm_settings_restart, 'restart site store global time')

        self.tm_settings_steam = self.get_key(self.content_settings_tm, 'steam')
        self.tm_sda_global_sleep = self.get_key(self.tm_settings_steam, 'steam send offers global time')
        self.tm_cancel_offers_global_sleep = self.get_key(self.tm_settings_steam, 'steam cancel offers global time')
        self.tm_cancel_offers_sites_name = self.get_key(self.tm_settings_steam, 'steam cancel offers sites name')  # list of dict

        self.tm_settings_history = self.get_key(self.content_settings_tm, 'history')
        self.tm_history_tg_id = self.get_key(self.tm_settings_history, 'history items sold tg id')
        self.tm_history_tg_token = self.get_key(self.tm_settings_history, 'history items sold tg token')
        if self.tm_history_tg_token:
            self.tm_history_tg_bot = telebot.TeleBot(self.tm_history_tg_token)
        self.tm_history_global_sleep = self.get_key(self.tm_settings_history, 'history global time')

        self.tm_settings_items = self.get_key(self.content_settings_tm, 'items')
        self.tm_add_to_sale_global_sleep = self.get_key(self.tm_settings_items, 'add to sale global time')
        self.tm_change_price_global_sleep = self.get_key(self.tm_settings_items, 'change price global time')





        # endregion

    def update_account_data_info(self):
        try:
            self.content_acc_data_list = self.get_all_docs_from_mongo_collection(self.acc_data_collection)
            self.content_acc_data_dict = self.get_dict_from_collection_list(self.content_acc_data_list,
                                                                         'username')
        except Exception as e:
            Logs.log(f'Error while updating data from mongo: {e}')

    def update_db_prices_and_setting(self):
        try:
            self.content_database_prices = self.get_first_doc_from_mongo_collection(self.database_prices_collection)
            self.content_database_settings = self.get_first_doc_from_mongo_collection(self.database_settings_collection)
        except Exception as e:
            Logs.log(f'Error while updating data from mongo: {e}')

    def create_merge_acc_for_parsing_and_acc_sittings(self):
        result = []
        try:
            unique_iterator = itertools.cycle(self.content_acc_for_parsing_list)
            for acc in self.content_acc_list:
                unique_acc = next(unique_iterator)
                result.append([acc, unique_acc])
            return result

        except Exception as e:
            Logs.log(f"Error during merging accounts: {e}")
            return result

    def search_in_merges_by_username(self, username):
        for sublist in self.content_merges:
            if sublist[0]['username'] == username:
                return sublist[1]
        return None

    def get_database(self, db_name):
        try:
            return self.client[db_name]
        except Exception as e:
            Logs.log(f"Error during receiving database {db_name}: {e}")
            return None

    @staticmethod
    def get_collection(database, collection_name):
        if database is None:
            return None
        try:
            return database[collection_name]
        except Exception as e:
            Logs.log(f"Error during receiving collection {collection_name}: {e}")
            return None

    @staticmethod
    def get_key(dictionary, key):
        try:
            if key in dictionary:
                dictionary = dictionary[key]
            else:
                if dictionary != {}:
                    Logs.log(f"Key '{key}' not found in {dictionary}")
            return dictionary
        except:
            return None

    @staticmethod
    def get_first_doc_from_mongo_collection(collection):
        result = collection.find_one()
        return result or {}

    @staticmethod
    def get_all_docs_from_mongo_collection(collection):
        results = collection.find({})
        results_list = []
        for result in results:
            results_list.append(result)
        return results_list

    @staticmethod
    def get_dict_from_collection_list(doc_list, key_name):
        results_dict = {}
        for doc in doc_list:
            account_name = doc.get(key_name)
            if account_name:
                results_dict[account_name] = doc
        return results_dict

