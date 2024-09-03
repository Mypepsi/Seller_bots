import telebot
import itertools
from pymongo import MongoClient
from bots_libraries.sellpy.logs import Logs, ExitException


class Mongo:
    def __init__(self, main_tg_info):
        self.client = MongoClient(  # Connecting to MongoDB
            "mongodb://127.0.0.1:27017",
            serverSelectionTimeoutMS=30000,  # Server selection timeout.
            connectTimeoutMS=30000,  # Connection timeout.
            socketTimeoutMS=30000,  # Read/write timeout.
            wtimeoutMS=30000,  # Write acknowledgment timeout.
            minPoolSize=0,  # Minimum connections in pool.
            maxPoolSize=10  # Maximum connections in pool.
        )

        self.tg_info = main_tg_info  # Initialization TG Info

        # region MongoDB
        self.seller_databases = self.get_database('Seller_DataBases')
        self.database_prices_collection = self.get_collection(self.seller_databases, 'database_prices')
        self.content_database_prices = None

        self.database_settings_collection = self.get_collection(self.seller_databases, 'database_settings')
        self.content_database_settings = None

        self.database_csgoempire_collection = self.get_collection(self.seller_databases, 'database_csgoempire')
        self.content_database_csgoempire = None

        self.database_csgo500_collection = self.get_collection(self.seller_databases, 'database_csgo500')
        self.content_database_csgo500 = None

        self.seller_settings = self.get_database('Seller_Settings')

        self.seller_accounts = self.get_database('Seller_Accounts')
        self.acc_settings_collection = self.get_collection(self.seller_accounts, 'account_settings')
        self.content_acc_settings_list = self.get_all_docs_from_mongo_collection(self.acc_settings_collection)
        self.content_acc_settings_dict = self.get_dict_from_collection_list(self.content_acc_settings_list, 'username')

        self.acc_data_collection = self.get_collection(self.seller_accounts, 'account_data')
        self.content_acc_data_list = self.get_all_docs_from_mongo_collection(self.acc_data_collection)
        self.content_acc_data_dict = self.get_dict_from_collection_list(self.content_acc_data_list, 'username')

        self.acc_for_parsing_collection = self.get_collection(self.seller_accounts, 'account_for_parsing')
        self.content_acc_for_parsing_list = self.get_all_docs_from_mongo_collection(self.acc_for_parsing_collection)

        self.content_merges = self.create_merge_info_for_parsing()

        self.seller_history = self.get_database('Seller_History')
        self.acc_history_collection = None
        # endregion

        # region Collection creator_settings
        if self.tg_info["bot name"] == 'Creator':
            self.creator_settings_collection = self.get_collection(self.seller_settings, 'creator_settings')
            self.content_creator_settings = self.get_first_doc_from_mongo_collection(self.creator_settings_collection)

            self.creator_settings_general = self.get_key(self.content_creator_settings, 'general')
            self.waiting_start_time = self.get_key(self.creator_settings_general, 'waiting start time')
            self.function_start_time = self.get_key(self.creator_settings_general, 'function start time')
            self.account_start_time = self.get_key(self.creator_settings_general, 'account start time')
            self.update_session_global_time = self.get_key(self.creator_settings_general, 'update session global time')
            self.proxy_url = f"https://{self.get_key(self.creator_settings_general, 'proxy url')}"
            self.proxy_global_time = self.get_key(self.creator_settings_general, 'proxy global time')
            self.mongodb_global_time = self.get_key(self.creator_settings_general, 'mongodb global time')

            self.creator_settings_database = self.get_key(self.content_creator_settings, 'database')
            self.db_prices_url = f"http://{self.get_key(self.creator_settings_database, 'db prices url')}"
            self.db_prices_validity_time = self.get_key(self.creator_settings_database, 'db prices validity time')
            self.db_prices_global_time = self.get_key(self.creator_settings_database, 'db prices global time')
            self.db_settings_url = f"http://{self.get_key(self.creator_settings_database, 'db settings url')}"
            self.db_settings_validity_time = self.get_key(self.creator_settings_database, 'db settings validity time')
            self.db_settings_global_time = self.get_key(self.creator_settings_database, 'db settings global time')

            self.creator_settings_steam = self.get_key(self.content_creator_settings, 'steam')
            self.steam_session_validity_time = self.get_key(self.creator_settings_steam, 'steam session validity time')
            self.steam_login_global_time = self.get_key(self.creator_settings_steam, 'steam login global time')
            self.steam_inventory_hashname_validity_time = self.get_key(self.creator_settings_steam, 'steam inventory hashname validity time')
            self.steam_inventory_global_time = self.get_key(self.creator_settings_steam, 'steam inventory global time')
            self.steam_access_token_global_time = self.get_key(self.creator_settings_steam, 'steam access token global time')
            self.steam_apikey_global_time = self.get_key(self.creator_settings_steam, 'steam apikey global time')

            self.creator_settings_restart = self.get_key(self.content_creator_settings, 'restart')
            self.restart_server_validity_time = self.get_key(self.creator_settings_restart, 'restart server validity time')
            self.restart_server_global_time = self.get_key(self.creator_settings_restart, 'restart server global time')
            self.restart_bots_name = self.get_key(self.creator_settings_restart, 'restart bots name')  # list of dict
            self.restart_bots_global_time = self.get_key(self.creator_settings_restart, 'restart bots global time')
        # endregion

        # region Collection tm_seller_settings
        elif self.tg_info["bot name"] == 'TM Seller':
            self.tm_settings_collection = self.get_collection(self.seller_settings, 'tm_seller_settings')
            self.content_tm_settings = self.get_first_doc_from_mongo_collection(self.tm_settings_collection)

            self.tm_settings_general = self.get_key(self.content_tm_settings, 'general')
            self.waiting_start_time = self.get_key(self.tm_settings_general, 'waiting start time')
            self.function_start_time = self.get_key(self.tm_settings_general, 'function start time')
            self.account_start_time = self.get_key(self.tm_settings_general, 'account start time')
            self.update_session_global_time = self.get_key(self.tm_settings_general, 'update session global time')
            self.site_url = f"https://{self.get_key(self.tm_settings_general, 'site url')}"
            self.site_apikey_global_time = self.get_key(self.tm_settings_general, 'site apikey global time')
            self.balance_transfer_global_time = self.get_key(self.tm_settings_general, 'balance transfer global time')
            self.site_name = self.get_key(self.tm_settings_general, 'site name')
            self.saleprice_bot_name = self.get_key(self.tm_settings_general, 'saleprice bot name')

            self.tm_settings_online = self.get_key(self.content_tm_settings, 'online')
            self.ping_global_time = self.get_key(self.tm_settings_online, 'ping global time')
            self.visible_store_max_number_of_inv_items = self.get_key(self.tm_settings_online, 'visible store max number of inv items')
            self.visible_store_global_time = self.get_key(self.tm_settings_online, 'visible store global time')

            self.tm_settings_items = self.get_key(self.content_tm_settings, 'items')
            self.add_to_sale_global_time = self.get_key(self.tm_settings_items, 'add to sale global time')
            self.change_price_global_time = self.get_key(self.tm_settings_items, 'change price global time')

            self.tm_settings_steam = self.get_key(self.content_tm_settings, 'steam')
            self.steam_send_offers_global_time = self.get_key(self.tm_settings_steam, 'steam send offers global time')
            self.steam_cancel_offers_sites_name = self.get_key(self.tm_settings_steam, 'steam cancel offers sites name')  # list of dict
            self.steam_cancel_offers_global_time = self.get_key(self.tm_settings_steam, 'steam cancel offers global time')

            self.tm_settings_history = self.get_key(self.content_tm_settings, 'history')
            self.history_tg_token = self.get_key(self.tm_settings_history, 'history tg token')
            self.history_tg_id = self.get_key(self.tm_settings_history, 'history tg id')
            self.history_global_time = self.get_key(self.tm_settings_history, 'history global time')
            if self.history_tg_token:
                self.history_tg_bot = telebot.TeleBot(self.history_tg_token)
                self.history_tg_info = {
                    'tg id': self.history_tg_id,
                    'tg bot': self.history_tg_bot,
                    'bot name': self.tg_info['bot name']
                }

            self.tm_settings_restart = self.get_key(self.content_tm_settings, 'restart')
            self.restart_store_global_time = self.get_key(self.tm_settings_restart, 'restart store global time')
            self.restart_server_validity_time = self.get_key(self.tm_settings_restart, 'restart server validity time')
            self.restart_server_global_time = self.get_key(self.tm_settings_restart, 'restart server global time')
            self.restart_bots_name = self.get_key(self.tm_settings_restart, 'restart bots name')  # list of dict
            self.restart_bots_global_time = self.get_key(self.tm_settings_restart, 'restart bots global time')
        # endregion

        # region Collection waxpeer_seller_settings
        elif self.tg_info["bot name"] == 'Waxpeer Seller':
            self.waxpeer_settings_collection = self.get_collection(self.seller_settings, 'waxpeer_seller_settings')
            self.content_waxpeer_settings = self.get_first_doc_from_mongo_collection(self.waxpeer_settings_collection)

            self.waxpeer_settings_general = self.get_key(self.content_waxpeer_settings, 'general')
            self.waiting_start_time = self.get_key(self.waxpeer_settings_general, 'waiting start time')
            self.function_start_time = self.get_key(self.waxpeer_settings_general, 'function start time')
            self.account_start_time = self.get_key(self.waxpeer_settings_general, 'account start time')
            self.update_session_global_time = self.get_key(self.waxpeer_settings_general, 'update session global time')
            self.site_url = f"https://{self.get_key(self.waxpeer_settings_general, 'site url')}"
            self.site_apikey_global = self.get_key(self.waxpeer_settings_general, 'site apikey global time')
            self.balance_transfer_global_time = self.get_key(self.waxpeer_settings_general, 'balance transfer global time')
            self.site_name = self.get_key(self.waxpeer_settings_general, 'site name')
            self.saleprice_bot_name = self.get_key(self.waxpeer_settings_general, 'saleprice bot name')

            self.waxpeer_settings_online = self.get_key(self.content_waxpeer_settings, 'online')
            self.ping_global_time = self.get_key(self.waxpeer_settings_online, 'ping global time')
            self.visible_store_max_number_of_inv_items = self.get_key(self.waxpeer_settings_online, 'visible store max number of inv items')
            self.visible_store_global_time = self.get_key(self.waxpeer_settings_online, 'visible store global time')

            self.waxpeer_settings_items = self.get_key(self.content_waxpeer_settings, 'items')
            self.add_to_sale_global_time = self.get_key(self.waxpeer_settings_items, 'add to sale global time')
            self.change_price_global_time = self.get_key(self.waxpeer_settings_items, 'change price global time')

            self.waxpeer_settings_steam = self.get_key(self.content_waxpeer_settings, 'steam')
            self.steam_send_offers_global_time = self.get_key(self.waxpeer_settings_steam, 'steam send offers global time')
            self.steam_cancel_offers_sites_name = self.get_key(self.waxpeer_settings_steam, 'steam cancel offers sites name')  # list of dict
            self.steam_cancel_offers_global_time = self.get_key(self.waxpeer_settings_steam, 'steam cancel offers global time')

            self.waxpeer_settings_history = self.get_key(self.content_waxpeer_settings, 'history')
            self.history_tg_token = self.get_key(self.waxpeer_settings_history, 'history tg token')
            self.history_tg_id = self.get_key(self.waxpeer_settings_history, 'history tg id')
            self.history_global_time = self.get_key(self.waxpeer_settings_history, 'history global time')
            if self.history_tg_token:
                self.history_tg_bot = telebot.TeleBot(self.history_tg_token)
                self.history_tg_info = {
                    'tg id': self.history_tg_id,
                    'tg bot': self.history_tg_bot,
                    'bot name': self.tg_info['bot name']
                }

            self.waxpeer_settings_restart = self.get_key(self.content_waxpeer_settings, 'restart')
            self.restart_store_global_time = self.get_key(self.waxpeer_settings_restart, 'restart store global time')
            self.restart_server_validity_time = self.get_key(self.waxpeer_settings_restart, 'restart server validity time')
            self.restart_server_global_time = self.get_key(self.waxpeer_settings_restart, 'restart server global time')
            self.restart_bots_name = self.get_key(self.waxpeer_settings_restart, 'restart bots name')  # list of dict
            self.restart_bots_global_time = self.get_key(self.waxpeer_settings_restart, 'restart bots global time')
        # endregion

        # region Collection csgoempire_seller_settings
        elif self.tg_info["bot name"] == 'CSGOEmpire Seller':
            self.csgoempire_settings_collection = self.get_collection(self.seller_settings, 'csgoempire_seller_settings')
            self.content_csgoempire_settings = self.get_first_doc_from_mongo_collection(self.csgoempire_settings_collection)

            self.csgoempire_settings_general = self.get_key(self.content_csgoempire_settings, 'general')
            self.waiting_start_time = self.get_key(self.csgoempire_settings_general, 'waiting start time')
            self.function_start_time = self.get_key(self.csgoempire_settings_general, 'function start time')
            self.account_start_time = self.get_key(self.csgoempire_settings_general, 'account start time')
            self.update_session_global_time = self.get_key(self.csgoempire_settings_general, 'update session global time')
            self.site_url = f"https://{self.get_key(self.csgoempire_settings_general, 'site url')}"
            self.site_apikey_global = self.get_key(self.csgoempire_settings_general, 'site apikey global time')
            self.balance_transfer_global_time = self.get_key(self.csgoempire_settings_general, 'balance transfer global time')
            self.site_name = self.get_key(self.csgoempire_settings_general, 'site name')
            self.saleprice_bot_name = self.get_key(self.csgoempire_settings_general, 'saleprice bot name')

            self.csgoempire_settings_online = self.get_key(self.content_csgoempire_settings, 'online')
            self.ping_global_time = self.get_key(self.csgoempire_settings_online, 'ping global time')
            self.visible_store_max_number_of_inv_items = self.get_key(self.csgoempire_settings_online, 'visible store max number of inv items')
            self.visible_store_global_time = self.get_key(self.csgoempire_settings_online, 'visible store global time')

            self.csgoempire_settings_items = self.get_key(self.content_csgoempire_settings, 'items')
            self.add_to_sale_global_time = self.get_key(self.csgoempire_settings_items, 'add to sale global time')
            self.change_price_global_time = self.get_key(self.csgoempire_settings_items, 'change price global time')

            self.csgoempire_settings_steam = self.get_key(self.content_csgoempire_settings, 'steam')
            self.steam_send_offers_global_time = self.get_key(self.csgoempire_settings_steam, 'steam send offers global time')
            self.steam_cancel_offers_sites_name = self.get_key(self.csgoempire_settings_steam, 'steam cancel offers sites name')  # list of dict
            self.steam_cancel_offers_global_time = self.get_key(self.csgoempire_settings_steam, 'steam cancel offers global time')

            self.csgoempire_settings_history = self.get_key(self.content_csgoempire_settings, 'history')
            self.history_tg_token = self.get_key(self.csgoempire_settings_history, 'history tg token')
            self.history_tg_id = self.get_key(self.csgoempire_settings_history, 'history tg id')
            self.history_global_time = self.get_key(self.csgoempire_settings_history, 'history global time')
            if self.history_tg_token:
                self.history_tg_bot = telebot.TeleBot(self.history_tg_token)
                self.history_tg_info = {
                    'tg id': self.history_tg_id,
                    'tg bot': self.history_tg_bot,
                    'bot name': self.tg_info['bot name']
                }

            self.csgoempire_settings_restart = self.get_key(self.content_csgoempire_settings, 'restart')
            self.restart_store_global_time = self.get_key(self.csgoempire_settings_restart, 'restart store global time')
            self.restart_server_validity_time = self.get_key(self.csgoempire_settings_restart, 'restart server validity time')
            self.restart_server_global_time = self.get_key(self.csgoempire_settings_restart, 'restart server global time')
            self.restart_bots_name = self.get_key(self.csgoempire_settings_restart, 'restart bots name')  # list of dict
            self.restart_bots_global_time = self.get_key(self.csgoempire_settings_restart, 'restart bots global time')
        # endregion

        # region Collection csgo500_seller_settings
        elif self.tg_info["bot name"] == 'CSGO500 Seller':
            self.csgo500_settings_collection = self.get_collection(self.seller_settings, 'csgo500_seller_settings')
            self.content_csgo500_settings = self.get_first_doc_from_mongo_collection(self.csgo500_settings_collection)

            self.csgo500_settings_general = self.get_key(self.content_csgo500_settings, 'general')
            self.waiting_start_time = self.get_key(self.csgo500_settings_general, 'waiting start time')
            self.function_start_time = self.get_key(self.csgo500_settings_general, 'function start time')
            self.account_start_time = self.get_key(self.csgo500_settings_general, 'account start time')
            self.update_session_global_time = self.get_key(self.csgo500_settings_general, 'update session global time')
            self.site_url = f"https://{self.get_key(self.csgo500_settings_general, 'site url')}"
            self.site_apikey_global = self.get_key(self.csgo500_settings_general, 'site apikey global time')
            self.balance_transfer_global_time = self.get_key(self.csgo500_settings_general, 'balance transfer global time')
            self.site_name = self.get_key(self.csgo500_settings_general, 'site name')
            self.saleprice_bot_name = self.get_key(self.csgo500_settings_general, 'saleprice bot name')

            self.csgo500_settings_online = self.get_key(self.content_csgo500_settings, 'online')
            self.ping_global_time = self.get_key(self.csgo500_settings_online, 'ping global time')
            self.visible_store_max_number_of_inv_items = self.get_key(self.csgo500_settings_online, 'visible store max number of inv items')
            self.visible_store_global_time = self.get_key(self.csgo500_settings_online, 'visible store global time')

            self.csgo500_settings_items = self.get_key(self.content_csgo500_settings, 'items')
            self.add_to_sale_global_time = self.get_key(self.csgo500_settings_items, 'add to sale global time')
            self.change_price_global_time = self.get_key(self.csgo500_settings_items, 'change price global time')

            self.csgo500_settings_steam = self.get_key(self.content_csgo500_settings, 'steam')
            self.steam_send_offers_global_time = self.get_key(self.csgo500_settings_steam, 'steam send offers global time')
            self.steam_cancel_offers_sites_name = self.get_key(self.csgo500_settings_steam, 'steam cancel offers sites name')  # list of dict
            self.steam_cancel_offers_global_time = self.get_key(self.csgo500_settings_steam, 'steam cancel offers global time')

            self.csgo500_settings_history = self.get_key(self.content_csgo500_settings, 'history')
            self.history_tg_token = self.get_key(self.csgo500_settings_history, 'history tg token')
            self.history_tg_id = self.get_key(self.csgo500_settings_history, 'history tg id')
            self.history_global_time = self.get_key(self.csgo500_settings_history, 'history global time')
            if self.history_tg_token:
                self.history_tg_bot = telebot.TeleBot(self.history_tg_token)
                self.history_tg_info = {
                    'tg id': self.history_tg_id,
                    'tg bot': self.history_tg_bot,
                    'bot name': self.tg_info['bot name']
                }

            self.csgo500_settings_restart = self.get_key(self.content_csgo500_settings, 'restart')
            self.restart_store_global_time = self.get_key(self.csgo500_settings_restart, 'restart store global time')
            self.restart_server_validity_time = self.get_key(self.csgo500_settings_restart, 'restart server validity time')
            self.restart_server_global_time = self.get_key(self.csgo500_settings_restart, 'restart server global time')
            self.restart_bots_name = self.get_key(self.csgo500_settings_restart, 'restart bots name')  # list of dict
            self.restart_bots_global_time = self.get_key(self.csgo500_settings_restart, 'restart bots global time')
        # endregion

        # region Collection shadowpay_seller_settings
        elif self.tg_info["bot name"] == 'ShadowPay Seller':
            self.shadowpay_settings_collection = self.get_collection(self.seller_settings, 'shadowpay_seller_settings')
            self.content_shadowpay_settings = self.get_first_doc_from_mongo_collection(self.shadowpay_settings_collection)

            self.shadowpay_settings_general = self.get_key(self.content_shadowpay_settings, 'general')
            self.waiting_start_time = self.get_key(self.shadowpay_settings_general, 'waiting start time')
            self.function_start_time = self.get_key(self.shadowpay_settings_general, 'function start time')
            self.account_start_time = self.get_key(self.shadowpay_settings_general, 'account start time')
            self.update_session_global_time = self.get_key(self.shadowpay_settings_general, 'update session global time')
            self.site_url = f"https://{self.get_key(self.shadowpay_settings_general, 'site url')}"
            self.site_apikey_global = self.get_key(self.shadowpay_settings_general, 'site apikey global time')
            self.balance_transfer_global_time = self.get_key(self.shadowpay_settings_general, 'balance transfer global time')
            self.site_name = self.get_key(self.shadowpay_settings_general, 'site name')
            self.saleprice_bot_name = self.get_key(self.shadowpay_settings_general, 'saleprice bot name')

            self.shadowpay_settings_online = self.get_key(self.content_shadowpay_settings, 'online')
            self.ping_global_time = self.get_key(self.shadowpay_settings_online, 'ping global time')
            self.visible_store_max_number_of_inv_items = self.get_key(self.shadowpay_settings_online,
                                                                      'visible store max number of inv items')
            self.visible_store_global_time = self.get_key(self.shadowpay_settings_online, 'visible store global time')

            self.shadowpay_settings_items = self.get_key(self.content_shadowpay_settings, 'items')
            self.add_to_sale_global_time = self.get_key(self.shadowpay_settings_items, 'add to sale global time')
            self.change_price_global_time = self.get_key(self.shadowpay_settings_items, 'change price global time')

            self.shadowpay_settings_steam = self.get_key(self.content_shadowpay_settings, 'steam')
            self.steam_send_offers_global_time = self.get_key(self.shadowpay_settings_steam, 'steam send offers global time')
            self.steam_cancel_offers_sites_name = self.get_key(self.shadowpay_settings_steam,
                                                               'steam cancel offers sites name')  # list of dict
            self.steam_cancel_offers_global_time = self.get_key(self.shadowpay_settings_steam,
                                                                'steam cancel offers global time')

            self.shadowpay_settings_history = self.get_key(self.content_shadowpay_settings, 'history')
            self.history_tg_token = self.get_key(self.shadowpay_settings_history, 'history tg token')
            self.history_tg_id = self.get_key(self.shadowpay_settings_history, 'history tg id')
            self.history_global_time = self.get_key(self.shadowpay_settings_history, 'history global time')
            if self.history_tg_token:
                self.history_tg_bot = telebot.TeleBot(self.history_tg_token)
                self.history_tg_info = {
                    'tg id': self.history_tg_id,
                    'tg bot': self.history_tg_bot,
                    'bot name': self.tg_info['bot name']
                }

            self.shadowpay_settings_restart = self.get_key(self.content_shadowpay_settings, 'restart')
            self.restart_store_global_time = self.get_key(self.shadowpay_settings_restart, 'restart store global time')
            self.restart_server_validity_time = self.get_key(self.shadowpay_settings_restart, 'restart server validity time')
            self.restart_server_global_time = self.get_key(self.shadowpay_settings_restart, 'restart server global time')
            self.restart_bots_name = self.get_key(self.shadowpay_settings_restart, 'restart bots name')  # list of dict
            self.restart_bots_global_time = self.get_key(self.shadowpay_settings_restart, 'restart bots global time')
        # endregion

        # region Collection buff_seller_settings
        elif self.tg_info["bot name"] == 'Buff Seller':
            self.buff_settings_collection = self.get_collection(self.seller_settings, 'buff_seller_settings')
            self.content_buff_settings = self.get_first_doc_from_mongo_collection(self.buff_settings_collection)

            self.buff_settings_general = self.get_key(self.content_buff_settings, 'general')
            self.waiting_start_time = self.get_key(self.buff_settings_general, 'waiting start time')
            self.function_start_time = self.get_key(self.buff_settings_general, 'function start time')
            self.account_start_time = self.get_key(self.buff_settings_general, 'account start time')
            self.update_session_global_time = self.get_key(self.buff_settings_general, 'update session global time')
            self.site_url = f"https://{self.get_key(self.buff_settings_general, 'site url')}"
            self.site_apikey_global = self.get_key(self.buff_settings_general, 'site cookie global time')
            self.balance_transfer_global_time = self.get_key(self.buff_settings_general, 'balance transfer global time')
            self.site_name = self.get_key(self.buff_settings_general, 'site name')
            self.saleprice_bot_name = self.get_key(self.buff_settings_general, 'saleprice bot name')

            self.buff_settings_online = self.get_key(self.content_buff_settings, 'online')
            self.ping_global_time = self.get_key(self.buff_settings_online, 'ping global time')
            self.visible_store_max_number_of_inv_items = self.get_key(self.buff_settings_online, 'visible store max number of inv items')
            self.visible_store_global_time = self.get_key(self.buff_settings_online, 'visible store global time')

            self.buff_settings_items = self.get_key(self.content_buff_settings, 'items')
            self.add_to_sale_global_time = self.get_key(self.buff_settings_items, 'add to sale global time')
            self.change_price_global_time = self.get_key(self.buff_settings_items, 'change price global time')

            self.buff_settings_steam = self.get_key(self.content_buff_settings, 'steam')
            self.steam_send_offers_global_time = self.get_key(self.buff_settings_steam, 'steam send offers global time')
            self.steam_cancel_offers_sites_name = self.get_key(self.buff_settings_steam, 'steam cancel offers sites name')  # list of dict
            self.steam_cancel_offers_global_time = self.get_key(self.buff_settings_steam, 'steam cancel offers global time')

            self.buff_settings_history = self.get_key(self.content_buff_settings, 'history')
            self.history_tg_token = self.get_key(self.buff_settings_history, 'history tg token')
            self.history_tg_id = self.get_key(self.buff_settings_history, 'history tg id')
            self.history_global_time = self.get_key(self.buff_settings_history, 'history global time')
            if self.history_tg_token:
                self.history_tg_bot = telebot.TeleBot(self.history_tg_token)
                self.history_tg_info = {
                    'tg id': self.history_tg_id,
                    'tg bot': self.history_tg_bot,
                    'bot name': self.tg_info['bot name']
                }

            self.buff_settings_restart = self.get_key(self.content_buff_settings, 'restart')
            self.restart_store_global_time = self.get_key(self.buff_settings_restart, 'restart store global time')
            self.restart_server_validity_time = self.get_key(self.buff_settings_restart, 'restart server validity time')
            self.restart_server_global_time = self.get_key(self.buff_settings_restart, 'restart server global time')
            self.restart_bots_name = self.get_key(self.buff_settings_restart, 'restart bots name')  # list of dict
            self.restart_bots_global_time = self.get_key(self.buff_settings_restart, 'restart bots global time')
        # endregion

        else:  # Initialization Parameters Error
            raise ExitException

    # region Mongo Info
    def get_database(self, db_name):
        try:
            return self.client[db_name]
        except:
            return None

    def get_collection(self, database, collection_name):
        try:
            if database is not None:
                return database[collection_name]
        except:
            pass
        return None

    @staticmethod
    def get_first_doc_from_mongo_collection(collection):
        try:
            result = collection.find_one()
            return result or {}
        except:
            return {}

    @staticmethod
    def get_all_docs_from_mongo_collection(collection):
        results_list = []
        try:
            results = collection.find({})
            for result in results:
                results_list.append(result)
        except:
            pass
        return results_list

    @staticmethod
    def get_dict_from_collection_list(doc_list, key_name):
        results_dict = {}
        try:
            for doc in doc_list:
                account_name = doc.get(key_name)
                if account_name:
                    results_dict[account_name] = doc
        except:
            pass
        return results_dict

    def get_key(self, dictionary, key):
        try:
            if key in dictionary:
                dictionary = dictionary[key]
                return dictionary
            else:
                if dictionary != {} and dictionary is not None:
                    Logs.notify(self.tg_info, f"MongoDB: Key '{key}' not found in {dictionary}", '')
        except:
            pass
        return None
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
            Logs.notify_except(self.tg_info, f"MongoDB: Error while creating Merge Info for Parsing: {e}", '')
        return result

    def search_in_merges_by_username(self, username):
        try:
            for sublist in self.content_merges:
                if sublist[0]['username'] == username:
                    return sublist[1]
        except Exception as e:
            Logs.notify_except(self.tg_info, f"MongoDB: Error searching in Merges Info by username: {e}", '')
        return None
    # endregion

    # region Price Info
    def get_information_for_price(self):
        try:
            database_setting_bots = self.content_database_settings['DataBaseSettings']['Sellers_SalePrice']['bots']
            seller_value = None
            for key, value in database_setting_bots.items():
                if self.saleprice_bot_name in key:
                    seller_value = value
                    break
            return seller_value
        except Exception as e:
            Logs.notify_except(self.tg_info, f"MongoDB: Error during receiving Sellers_SalePrice: {e}", '')
            return None

    @staticmethod
    def find_matching_key(wanted, dictionary):
        try:
            keys = sorted([float(k) for k in dictionary.keys()])
            found_key = None
            for i in range(len(keys) - 1):
                if keys[i] <= wanted < keys[i + 1]:
                    if keys[i].is_integer():
                        found_key = str(int(keys[i]))
                    else:
                        found_key = str(keys[i])
                    break
            if found_key is None and wanted >= keys[-1]:
                if keys[-1].is_integer():
                    found_key = str(int(keys[-1]))
                else:
                    found_key = str(keys[-1])
            return found_key
        except:
            return None
    # endregion

    # region Update Info
    def update_database_info(self, prices=False, settings=False, csgoempire=False, csgo500=False):
        try:
            if prices:
                database_prices = self.get_first_doc_from_mongo_collection(self.database_prices_collection)
                if database_prices:
                    self.content_database_prices = database_prices
            if settings:
                database_settings = self.get_first_doc_from_mongo_collection(self.database_settings_collection)
                if database_settings:
                    self.content_database_settings = database_settings
            if csgoempire:
                database_csgoempire = self.get_first_doc_from_mongo_collection(self.database_csgoempire_collection)
                if database_csgoempire:
                    self.content_database_csgoempire = database_csgoempire
            if csgo500:
                database_csgo500 = self.get_first_doc_from_mongo_collection(self.database_csgo500_collection)
                if database_csgo500:
                    self.content_database_csgo500 = database_csgo500
        except:
            pass

    def update_account_settings_info(self):
        try:
            acc_settings_list = self.get_all_docs_from_mongo_collection(self.acc_settings_collection)
            if acc_settings_list:
                self.content_acc_settings_list = acc_settings_list
            acc_settings_dict = self.get_dict_from_collection_list(self.content_acc_settings_list, 'username')
            if acc_settings_dict:
                self.content_acc_settings_dict = acc_settings_dict
        except:
            pass

    def update_account_data_info(self):
        try:
            acc_data_list = self.get_all_docs_from_mongo_collection(self.acc_data_collection)
            if acc_data_list:
                self.content_acc_data_list = acc_data_list
            acc_data_dict = self.get_dict_from_collection_list(self.content_acc_data_list, 'username')
            if acc_data_dict:
                self.content_acc_data_dict = acc_data_dict
        except:
            pass

    # endregion
