from pymongo import MongoClient
from bots_libraries.sellpy.logs import Logs
import telebot
import itertools


class Mongo:
    def __init__(self):

        self.client = MongoClient("mongodb://127.0.0.1:27017")

        # region MongoDB
        self.database = self.get_database('Seller_DataBases')
        self.database_prices_collection = self.get_collection(self.database, 'database_prices')
        self.database_settings_collection = self.get_collection(self.database, 'database_settings')
        self.database_ip_collection = self.get_collection(self.database, 'server_ip_address')

        self.content_database_prices = self.get_first_doc_from_mongo_collection(self.database_prices_collection)
        self.content_database_settings = self.get_first_doc_from_mongo_collection(self.database_settings_collection)
        self.content_database_ip = self.get_first_doc_from_mongo_collection(self.database_ip_collection)


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
        self.content_acc_data_dict = self.get_dict_from_collection_list(self.content_acc_data_list, 'username')

        self.acc_for_parsing_collection = self.get_collection(self.accs, 'account_for_parsing')
        self.content_acc_for_parsing_list = self.get_all_docs_from_mongo_collection(self.acc_for_parsing_collection)

        self.content_merges = self.create_merge_info_for_parsing()
        # endregion



        # region Collection  creator_settings
        self.creator_settings_general = self.get_key(self.content_settings_creator, 'general')
        self.creator_sleep_before_start = self.get_key(self.creator_settings_general, 'waiting start time')
        self.creator_sleep_between_threads = self.get_key(self.creator_settings_general, 'thread start time')

        self.creator_settings_telegram = self.get_key(self.content_settings_creator, 'telegram')
        self.creator_tg_token = self.get_key(self.creator_settings_telegram, 'tg token')
        self.creator_tg_id = self.get_key(self.creator_settings_telegram, 'tg id')
        self.creator_tg_bot_name = self.get_key(self.creator_settings_telegram, 'tg bot name')

        self.creator_settings_sellpy = self.get_key(self.content_settings_creator, 'sellpy')
        self.creator_sellpy_tg_token = self.get_key(self.creator_settings_sellpy, 'sellpy tg token')
        self.creator_sellpy_tg_id = self.get_key(self.creator_settings_sellpy, 'sellpy tg id')

        self.creator_settings_database = self.get_key(self.content_settings_creator, 'database')
        self.creator_db_prices_url = f"http://{self.get_key(self.creator_settings_database, 'db prices url')}"
        self.creator_db_settings_url = f"http://{self.get_key(self.creator_settings_database, 'db settings url')}"
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
        self.creator_proxy_check_url = f"https://{self.get_key(self.creator_settings_proxy, 'proxy url')}"
        self.creator_proxy_global_sleep = self.get_key(self.creator_settings_proxy, 'proxy global time')

        self.creator_settings_restart = self.get_key(self.content_settings_creator, 'restart')
        self.creator_restart_time_sleep = self.get_key(self.creator_settings_restart, 'restart server validity time')
        self.creator_restart_server_global_sleep = self.get_key(self.creator_settings_restart, 'restart server global time')
        self.creator_restart_bots_global_sleep = self.get_key(self.creator_settings_restart, 'restart bots global time')
        self.creator_restart_info_bots = self.get_key(self.creator_settings_restart, 'restart bots name')  # list of dict

        # endregion



        # region Collection tm_seller_settings
        self.tm_settings_general = self.get_key(self.content_settings_tm, 'general')
        self.tm_sleep_before_start = self.get_key(self.tm_settings_general, 'waiting start time')
        self.tm_sleep_between_threads = self.get_key(self.tm_settings_general, 'thread start time')
        self.tm_thread_function_sleep = self.get_key(self.tm_settings_general, 'thread function time')
        self.tm_url = self.get_key(self.tm_settings_general, 'site url')
        self.tm_transfer_global_sleep = self.get_key(self.tm_settings_general, 'money transfer global time')
        self.tm_api_key_checker_global_sleep = self.get_key(self.tm_settings_general, 'site apikey global time')

        self.tm_settings_telegram = self.get_key(self.content_settings_tm, 'telegram')
        self.tm_tg_id = self.get_key(self.tm_settings_telegram, 'tg id')
        self.tm_tg_token = self.get_key(self.tm_settings_telegram, 'tg token')
        self.tm_tg_bot_name = self.get_key(self.tm_settings_telegram, 'tg bot name')

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
        self.tm_history_tg_id = self.get_key(self.tm_settings_history, 'history tg id')
        self.tm_history_tg_token = self.get_key(self.tm_settings_history, 'history tg token')
        self.tm_history_global_sleep = self.get_key(self.tm_settings_history, 'history global time')

        self.tm_settings_items = self.get_key(self.content_settings_tm, 'items')
        self.tm_add_to_sale_global_sleep = self.get_key(self.tm_settings_items, 'add to sale global time')
        self.tm_change_price_global_sleep = self.get_key(self.tm_settings_items, 'change price global time')

        # endregion


        # region Telegram Info
        if self.creator_sellpy_tg_token:
            self.creator_sellpy_tg_bot = telebot.TeleBot(self.creator_sellpy_tg_token)
        self.sellpy_tg_info = {
            'tg id': self.creator_sellpy_tg_id,
            'tg bot': self.creator_sellpy_tg_bot,
            'bot name': None
        }

        if self.creator_tg_token:
            self.creator_tg_bot = telebot.TeleBot(self.creator_tg_token)
        self.creator_tg_info = {
            'tg id': self.creator_tg_id,
            'tg bot': self.creator_tg_bot,
            'bot name': self.creator_tg_bot_name
        }

        if self.tm_tg_token:
            self.tm_tg_bot = telebot.TeleBot(self.tm_tg_token)
        self.tm_tg_info = {
            'tg id': self.tm_tg_id,
            'tg bot': self.tm_tg_bot,
            'bot name': self.tm_tg_bot_name
        }

        if self.tm_history_tg_token:
            self.tm_history_tg_bot = telebot.TeleBot(self.tm_history_tg_token)
        self.tm_history_tg_info = {
            'tg id': self.tm_history_tg_id,
            'tg bot': self.tm_history_tg_bot,
            'bot name': self.tm_tg_bot_name
        }

        # endregion

        # region Default Params
        self.acc_history_collection = None
        self.rate = 0
        self.commission = 0

        # endregion

    # region Update Info
    def update_account_settings_info(self):
        try:
            self.content_acc_list = self.get_all_docs_from_mongo_collection(self.acc_data_collection)
            self.content_acc_dict = self.get_dict_from_collection_list(self.content_acc_data_list,
                                                                         'username')
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f'Error while updating Accounts Settings: {e}', '')

    def update_account_data_info(self):
        try:
            self.content_acc_data_list = self.get_all_docs_from_mongo_collection(self.acc_data_collection)
            self.content_acc_data_dict = self.get_dict_from_collection_list(self.content_acc_data_list,
                                                                         'username')
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f'Error while updating Accounts Data: {e}', '')


    def update_db_prices_and_setting(self):
        try:
            self.content_database_prices = self.get_first_doc_from_mongo_collection(self.database_prices_collection)
            self.content_database_settings = self.get_first_doc_from_mongo_collection(self.database_settings_collection)
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f'Error while updating DataBase Prices, Settings: {e}', '')

    # endregion



    # region Merge Info
    def create_merge_info_for_parsing(self):
        result = []
        try:
            unique_iterator = itertools.cycle(self.content_acc_for_parsing_list)
            for acc in self.content_acc_data_list:
                unique_acc = next(unique_iterator)
                result.append([acc, unique_acc])
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f"Error while сreating Merge Info for Parsing: {e}", '')
        return result

    def search_in_merges_by_username(self, username):
        try:
            for sublist in self.content_merges:
                if sublist[0]['username'] == username:
                    return sublist[1]
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f"Error searching in Merges Info by username: {e}", '')
        return None
    #endregion



    # region Price Info
    @staticmethod
    def find_matching_key(wanted, dictionary):
        try:
            keys = sorted([float(k) for k in dictionary.keys()])
            found_key = None
            for i in range(len(keys) - 1):
                if wanted >= keys[i]:
                    found_key = str(int(keys[i])) if keys[i].is_integer() else str(keys[i])
                elif keys[i] <= wanted < keys[i + 1]:
                    if keys[i].is_integer():
                        found_key = str(int(keys[i]))
                    else:
                        found_key = str(keys[i])
                    break
            if found_key is None and wanted >= keys[-1]:
                found_key = str(keys[-1])
            return found_key
        except:
            return None

    def taking_information_for_price(self, name_of_seller):
        try:
            database_setting_bots = self.content_database_settings['DataBaseSettings']['Sellers_SalePrice']['bots']
            seller_value = None
            for key, value in database_setting_bots.items():
                if name_of_seller in key:
                    seller_value = value
                    break
            return seller_value
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f"Error during receiving Sellers_SalePrice: {e}", '')
            return None
    #endregion



    # region Mongo Info
    def get_database(self, db_name):
        try:
            return self.client[db_name]
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f"Error during receiving {db_name} database: {e}", '')
            return None

    def get_collection(self, database, collection_name):
        if database is None:
            return None
        try:
            return database[collection_name]
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f"Error during receiving {collection_name} collection: {e}", '')
            return None

    @staticmethod
    def get_key(dictionary, key):
        try:
            if key in dictionary:
                dictionary = dictionary[key]
            else:
                if dictionary != {}:
                    Logs.log(f"Key '{key}' not found in {dictionary}", '')
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
    #endregion


