import telebot
import itertools
from pymongo import MongoClient
from bots_libraries.sellpy.logs import Logs


class Mongo:
    def __init__(self, main_tg_info):
        self.client = MongoClient(
            "mongodb://127.0.0.1:27017",
            serverSelectionTimeoutMS=30000,  # Server selection timeout.
            connectTimeoutMS=30000,  # Connection timeout.
            socketTimeoutMS=30000,  # Read/write timeout.
            wtimeoutMS=30000,  # Write acknowledgment timeout.
            minPoolSize=0,  # Minimum connections in pool.
            maxPoolSize=10  # Maximum connections in pool.
        )


        # region MongoDB
        self.database = self.get_database('Seller_DataBases')
        self.database_prices_collection = self.get_collection(self.database, 'database_prices')
        self.content_database_prices = self.get_first_doc_from_mongo_collection(self.database_prices_collection)

        self.database_settings_collection = self.get_collection(self.database, 'database_settings')
        self.content_database_settings = self.get_first_doc_from_mongo_collection(self.database_settings_collection)

        self.settings = self.get_database('Seller_Settings')
        self.creator_settings_collection = self.get_collection(self.settings, 'creator_settings')
        self.content_creator_settings = self.get_first_doc_from_mongo_collection(self.creator_settings_collection)

        self.tm_settings_collection = self.get_collection(self.settings, 'tm_seller_settings')
        self.content_tm_settings = self.get_first_doc_from_mongo_collection(self.tm_settings_collection)

        self.waxpeer_settings_collection = self.get_collection(self.settings, 'waxpeer_seller_settings')
        self.content_waxpeer_settings = self.get_first_doc_from_mongo_collection(self.waxpeer_settings_collection)

        self.csgoempire_settings_collection = self.get_collection(self.settings, 'csgoempire_seller_settings')
        self.content_csgoempire_settings = self.get_first_doc_from_mongo_collection(self.csgoempire_settings_collection)

        self.csgo500_settings_collection = self.get_collection(self.settings, 'csgo500_seller_settings')
        self.content_csgo500_settings = self.get_first_doc_from_mongo_collection(self.csgo500_settings_collection)

        self.shadowpay_settings_collection = self.get_collection(self.settings, 'shadowpay_seller_settings')
        self.content_shadowpay_settings = self.get_first_doc_from_mongo_collection(self.shadowpay_settings_collection)

        self.buff_settings_collection = self.get_collection(self.settings, 'buff_seller_settings')
        self.content_buff_settings = self.get_first_doc_from_mongo_collection(self.buff_settings_collection)


        self.history = self.get_database('Seller_History')


        self.accs = self.get_database('Seller_Accounts')
        self.acc_settings_collection = self.get_collection(self.accs, 'account_settings')
        self.content_acc_settings_list = self.get_all_docs_from_mongo_collection(self.acc_settings_collection)
        self.content_acc_settings_dict = self.get_dict_from_collection_list(self.content_acc_settings_list, 'username')

        self.acc_data_collection = self.get_collection(self.accs, 'account_data')
        self.content_acc_data_list = self.get_all_docs_from_mongo_collection(self.acc_data_collection)
        self.content_acc_data_dict = self.get_dict_from_collection_list(self.content_acc_data_list, 'username')

        self.acc_for_parsing_collection = self.get_collection(self.accs, 'account_for_parsing')
        self.content_acc_for_parsing_list = self.get_all_docs_from_mongo_collection(self.acc_for_parsing_collection)

        self.content_merges = self.create_merge_info_for_parsing()
        # endregion


        # region Collection creator_settings
        self.creator_settings_telegram = self.get_key(self.content_creator_settings, 'telegram')
        self.creator_tg_token = self.get_key(self.creator_settings_telegram, 'tg token')
        self.creator_tg_id = self.get_key(self.creator_settings_telegram, 'tg id')
        self.creator_tg_bot_name = self.get_key(self.creator_settings_telegram, 'tg bot name')

        self.creator_settings_general = self.get_key(self.content_creator_settings, 'general')
        self.creator_waiting_start_time = self.get_key(self.creator_settings_general, 'waiting start time')
        self.creator_thread_start_time = self.get_key(self.creator_settings_general, 'thread start time')
        self.creator_mongodb_global_time = self.get_key(self.creator_settings_general, 'mongodb global time')

        self.creator_settings_database = self.get_key(self.content_creator_settings, 'database')
        self.creator_db_prices_url = f"http://{self.get_key(self.creator_settings_database, 'db prices url')}"
        self.creator_db_prices_validity_time = self.get_key(self.creator_settings_database, 'db prices validity time')
        self.creator_db_prices_global_time = self.get_key(self.creator_settings_database, 'db prices global time')
        self.creator_db_settings_url = f"http://{self.get_key(self.creator_settings_database, 'db settings url')}"
        self.creator_db_settings_validity_time = self.get_key(self.creator_settings_database, 'db settings validity time')
        self.creator_db_settings_global_time = self.get_key(self.creator_settings_database, 'db settings global time')

        self.creator_settings_steam = self.get_key(self.content_creator_settings, 'steam')
        self.creator_steam_session_validity_time = self.get_key(self.creator_settings_steam, 'steam session validity time')
        self.creator_steam_session_global_time = self.get_key(self.creator_settings_steam, 'steam session global time')
        self.creator_steam_inventory_hashname_validity_time = self.get_key(self.creator_settings_steam, 'steam inventory hashname validity time')
        self.creator_steam_inventory_global_time = self.get_key(self.creator_settings_steam, 'steam inventory global time')
        self.creator_steam_access_token_global_time = self.get_key(self.creator_settings_steam, 'steam access token global time')
        self.creator_steam_apikey_global_time = self.get_key(self.creator_settings_steam, 'steam apikey global time')

        self.creator_settings_proxy = self.get_key(self.content_creator_settings, 'proxy')
        self.creator_proxy_url = f"https://{self.get_key(self.creator_settings_proxy, 'proxy url')}"
        self.creator_proxy_global_time = self.get_key(self.creator_settings_proxy, 'proxy global time')

        self.creator_settings_restart = self.get_key(self.content_creator_settings, 'restart')
        self.creator_restart_server_validity_time = self.get_key(self.creator_settings_restart, 'restart server validity time')
        self.creator_restart_server_global_time = self.get_key(self.creator_settings_restart, 'restart server global time')
        self.creator_restart_bots_name = self.get_key(self.creator_settings_restart, 'restart bots name')  # list of dict
        self.creator_restart_bots_global_time = self.get_key(self.creator_settings_restart, 'restart bots global time')
        # endregion


        # region Collection tm_seller_settings
        self.tm_settings_telegram = self.get_key(self.content_tm_settings, 'telegram')
        self.tm_tg_token = self.get_key(self.tm_settings_telegram, 'tg token')
        self.tm_tg_id = self.get_key(self.tm_settings_telegram, 'tg id')
        self.tm_tg_bot_name = self.get_key(self.tm_settings_telegram, 'tg bot name')

        self.tm_settings_general = self.get_key(self.content_tm_settings, 'general')
        self.tm_waiting_start_time = self.get_key(self.tm_settings_general, 'waiting start time')
        self.tm_thread_start_time = self.get_key(self.tm_settings_general, 'thread start time')
        self.tm_thread_function_time = self.get_key(self.tm_settings_general, 'thread function time')
        self.tm_url = f"https://{self.get_key(self.tm_settings_general, 'url')}"
        self.tm_site_apikey_global_time = self.get_key(self.tm_settings_general, 'site apikey global time')
        self.tm_balance_transfer_global_time = self.get_key(self.tm_settings_general, 'balance transfer global time')
        self.tm_sale_price_bot_name = self.get_key(self.tm_settings_general, 'sale price bot name')

        self.tm_settings_online = self.get_key(self.content_tm_settings, 'online')
        self.tm_ping_global_time = self.get_key(self.tm_settings_online, 'ping global time')
        self.tm_visible_store_max_number_of_inv_items = self.get_key(self.tm_settings_online, 'visible store max number of inv items')
        self.tm_visible_store_global_time = self.get_key(self.tm_settings_online, 'visible store global time')

        self.tm_settings_items = self.get_key(self.content_tm_settings, 'items')
        self.tm_add_to_sale_global_time = self.get_key(self.tm_settings_items, 'add to sale global time')
        self.tm_change_price_global_time = self.get_key(self.tm_settings_items, 'change price global time')

        self.tm_settings_steam = self.get_key(self.content_tm_settings, 'steam')
        self.tm_steam_send_offers_global_time = self.get_key(self.tm_settings_steam, 'steam send offers global time')
        self.tm_steam_cancel_offers_sites_name = self.get_key(self.tm_settings_steam, 'steam cancel offers sites name')  # list of dict
        self.tm_steam_cancel_offers_global_time = self.get_key(self.tm_settings_steam, 'steam cancel offers global time')

        self.tm_settings_history = self.get_key(self.content_tm_settings, 'history')
        self.tm_history_tg_token = self.get_key(self.tm_settings_history, 'history tg token')
        self.tm_history_tg_id = self.get_key(self.tm_settings_history, 'history tg id')
        self.tm_history_global_time = self.get_key(self.tm_settings_history, 'history global time')

        self.tm_settings_restart = self.get_key(self.content_tm_settings, 'restart')
        self.tm_restart_store_global_time = self.get_key(self.tm_settings_restart, 'restart store global time')
        self.tm_restart_server_validity_time = self.get_key(self.tm_settings_restart, 'restart server validity time')
        self.tm_restart_server_global_time = self.get_key(self.tm_settings_restart, 'restart server global time')
        self.tm_restart_bots_name = self.get_key(self.tm_settings_restart, 'restart bots name')  # list of dict
        self.tm_restart_bots_global_time = self.get_key(self.tm_settings_restart, 'restart bots global time')
        # endregion

        # region Collection waxpeer_seller_settings
        self.waxpeer_settings_telegram = self.get_key(self.content_waxpeer_settings, 'telegram')
        self.waxpeer_tg_token = self.get_key(self.waxpeer_settings_telegram, 'tg token')
        self.waxpeer_tg_id = self.get_key(self.waxpeer_settings_telegram, 'tg id')
        self.waxpeer_tg_bot_name = self.get_key(self.waxpeer_settings_telegram, 'tg bot name')

        self.waxpeer_settings_general = self.get_key(self.content_waxpeer_settings, 'general')
        self.waxpeer_waiting_start_time = self.get_key(self.waxpeer_settings_general, 'waiting start time')
        self.waxpeer_thread_start_time = self.get_key(self.waxpeer_settings_general, 'thread start time')
        self.waxpeer_thread_function_time = self.get_key(self.waxpeer_settings_general, 'thread function time')
        self.waxpeer_url = f"https://{self.get_key(self.waxpeer_settings_general, 'url')}"
        self.waxpeer_site_apikey_global_time = self.get_key(self.waxpeer_settings_general, 'site apikey global time')
        self.waxpeer_balance_transfer_global_time = self.get_key(self.waxpeer_settings_general, 'balance transfer global time')
        self.waxpeer_sale_price_bot_name = self.get_key(self.waxpeer_settings_general, 'sale price bot name')

        self.waxpeer_settings_online = self.get_key(self.content_waxpeer_settings, 'online')
        self.waxpeer_ping_global_time = self.get_key(self.waxpeer_settings_online, 'ping global time')
        self.waxpeer_visible_store_max_number_of_inv_items = self.get_key(self.waxpeer_settings_online, 'visible store max number of inv items')
        self.waxpeer_visible_store_global_time = self.get_key(self.waxpeer_settings_online, 'visible store global time')

        self.waxpeer_settings_items = self.get_key(self.content_waxpeer_settings, 'items')
        self.waxpeer_add_to_sale_global_time = self.get_key(self.waxpeer_settings_items, 'add to sale global time')
        self.waxpeer_change_price_global_time = self.get_key(self.waxpeer_settings_items, 'change price global time')

        self.waxpeer_settings_steam = self.get_key(self.content_waxpeer_settings, 'steam')
        self.waxpeer_steam_send_offers_global_time = self.get_key(self.waxpeer_settings_steam, 'steam send offers global time')
        self.waxpeer_steam_cancel_offers_sites_name = self.get_key(self.waxpeer_settings_steam, 'steam cancel offers sites name')  # list of dict
        self.waxpeer_steam_cancel_offers_global_time = self.get_key(self.waxpeer_settings_steam, 'steam cancel offers global time')

        self.waxpeer_settings_history = self.get_key(self.content_waxpeer_settings, 'history')
        self.waxpeer_history_tg_token = self.get_key(self.waxpeer_settings_history, 'history tg token')
        self.waxpeer_history_tg_id = self.get_key(self.waxpeer_settings_history, 'history tg id')
        self.waxpeer_history_global_time = self.get_key(self.waxpeer_settings_history, 'history global time')

        self.waxpeer_settings_restart = self.get_key(self.content_waxpeer_settings, 'restart')
        self.waxpeer_restart_store_global_time = self.get_key(self.waxpeer_settings_restart, 'restart store global time')
        self.waxpeer_restart_server_validity_time = self.get_key(self.waxpeer_settings_restart, 'restart server validity time')
        self.waxpeer_restart_server_global_time = self.get_key(self.waxpeer_settings_restart, 'restart server global time')
        self.waxpeer_restart_bots_name = self.get_key(self.waxpeer_settings_restart, 'restart bots name')  # list of dict
        self.waxpeer_restart_bots_global_time = self.get_key(self.waxpeer_settings_restart, 'restart bots global time')
        # endregion

        # region Collection csgoempire_seller_settings
        self.csgoempire_settings_telegram = self.get_key(self.content_csgoempire_settings, 'telegram')
        self.csgoempire_tg_token = self.get_key(self.csgoempire_settings_telegram, 'tg token')
        self.csgoempire_tg_id = self.get_key(self.csgoempire_settings_telegram, 'tg id')
        self.csgoempire_tg_bot_name = self.get_key(self.csgoempire_settings_telegram, 'tg bot name')

        self.csgoempire_settings_general = self.get_key(self.content_csgoempire_settings, 'general')
        self.csgoempire_waiting_start_time = self.get_key(self.csgoempire_settings_general, 'waiting start time')
        self.csgoempire_thread_start_time = self.get_key(self.csgoempire_settings_general, 'thread start time')
        self.csgoempire_thread_function_time = self.get_key(self.csgoempire_settings_general, 'thread function time')
        self.csgoempire_url = f"https://{self.get_key(self.csgoempire_settings_general, 'url')}"
        self.csgoempire_site_apikey_global_time = self.get_key(self.csgoempire_settings_general, 'site apikey global time')
        self.csgoempire_balance_transfer_global_time = self.get_key(self.csgoempire_settings_general, 'balance transfer global time')
        self.csgoempire_sale_price_bot_name = self.get_key(self.csgoempire_settings_general, 'sale price bot name')

        self.csgoempire_settings_online = self.get_key(self.content_csgoempire_settings, 'online')
        self.csgoempire_ping_global_time = self.get_key(self.csgoempire_settings_online, 'ping global time')
        self.csgoempire_visible_store_max_number_of_inv_items = self.get_key(self.csgoempire_settings_online, 'visible store max number of inv items')
        self.csgoempire_visible_store_global_time = self.get_key(self.csgoempire_settings_online, 'visible store global time')

        self.csgoempire_settings_items = self.get_key(self.content_csgoempire_settings, 'items')
        self.csgoempire_add_to_sale_global_time = self.get_key(self.csgoempire_settings_items, 'add to sale global time')
        self.csgoempire_change_price_global_time = self.get_key(self.csgoempire_settings_items, 'change price global time')

        self.csgoempire_settings_steam = self.get_key(self.content_csgoempire_settings, 'steam')
        self.csgoempire_steam_send_offers_global_time = self.get_key(self.csgoempire_settings_steam, 'steam send offers global time')
        self.csgoempire_steam_cancel_offers_sites_name = self.get_key(self.csgoempire_settings_steam, 'steam cancel offers sites name')  # list of dict
        self.csgoempire_steam_cancel_offers_global_time = self.get_key(self.csgoempire_settings_steam, 'steam cancel offers global time')

        self.csgoempire_settings_history = self.get_key(self.content_csgoempire_settings, 'history')
        self.csgoempire_history_tg_token = self.get_key(self.csgoempire_settings_history, 'history tg token')
        self.csgoempire_history_tg_id = self.get_key(self.csgoempire_settings_history, 'history tg id')
        self.csgoempire_history_global_time = self.get_key(self.csgoempire_settings_history, 'history global time')

        self.csgoempire_settings_restart = self.get_key(self.content_csgoempire_settings, 'restart')
        self.csgoempire_restart_store_global_time = self.get_key(self.csgoempire_settings_restart, 'restart store global time')
        self.csgoempire_restart_server_validity_time = self.get_key(self.csgoempire_settings_restart, 'restart server validity time')
        self.csgoempire_restart_server_global_time = self.get_key(self.csgoempire_settings_restart, 'restart server global time')
        self.csgoempire_restart_bots_name = self.get_key(self.csgoempire_settings_restart, 'restart bots name')  # list of dict
        self.csgoempire_restart_bots_global_time = self.get_key(self.csgoempire_settings_restart, 'restart bots global time')
        # endregion

        # region Collection csgo500_seller_settings
        self.csgo500_settings_telegram = self.get_key(self.content_csgo500_settings, 'telegram')
        self.csgo500_tg_token = self.get_key(self.csgo500_settings_telegram, 'tg token')
        self.csgo500_tg_id = self.get_key(self.csgo500_settings_telegram, 'tg id')
        self.csgo500_tg_bot_name = self.get_key(self.csgo500_settings_telegram, 'tg bot name')

        self.csgo500_settings_general = self.get_key(self.content_csgo500_settings, 'general')
        self.csgo500_waiting_start_time = self.get_key(self.csgo500_settings_general, 'waiting start time')
        self.csgo500_thread_start_time = self.get_key(self.csgo500_settings_general, 'thread start time')
        self.csgo500_thread_function_time = self.get_key(self.csgo500_settings_general, 'thread function time')
        self.csgo500_url = f"https://{self.get_key(self.csgo500_settings_general, 'url')}"
        self.csgo500_site_apikey_global_time = self.get_key(self.csgo500_settings_general, 'site apikey global time')
        self.csgo500_balance_transfer_global_time = self.get_key(self.csgo500_settings_general, 'balance transfer global time')
        self.csgo500_sale_price_bot_name = self.get_key(self.csgo500_settings_general, 'sale price bot name')

        self.csgo500_settings_online = self.get_key(self.content_csgo500_settings, 'online')
        self.csgo500_ping_global_time = self.get_key(self.csgo500_settings_online, 'ping global time')
        self.csgo500_visible_store_max_number_of_inv_items = self.get_key(self.csgo500_settings_online, 'visible store max number of inv items')
        self.csgo500_visible_store_global_time = self.get_key(self.csgo500_settings_online, 'visible store global time')

        self.csgo500_settings_items = self.get_key(self.content_csgo500_settings, 'items')
        self.csgo500_add_to_sale_global_time = self.get_key(self.csgo500_settings_items, 'add to sale global time')
        self.csgo500_change_price_global_time = self.get_key(self.csgo500_settings_items, 'change price global time')

        self.csgo500_settings_steam = self.get_key(self.content_csgo500_settings, 'steam')
        self.csgo500_steam_send_offers_global_time = self.get_key(self.csgo500_settings_steam, 'steam send offers global time')
        self.csgo500_steam_cancel_offers_sites_name = self.get_key(self.csgo500_settings_steam, 'steam cancel offers sites name')  # list of dict
        self.csgo500_steam_cancel_offers_global_time = self.get_key(self.csgo500_settings_steam, 'steam cancel offers global time')

        self.csgo500_settings_history = self.get_key(self.content_csgo500_settings, 'history')
        self.csgo500_history_tg_token = self.get_key(self.csgo500_settings_history, 'history tg token')
        self.csgo500_history_tg_id = self.get_key(self.csgo500_settings_history, 'history tg id')
        self.csgo500_history_global_time = self.get_key(self.csgo500_settings_history, 'history global time')

        self.csgo500_settings_restart = self.get_key(self.content_csgo500_settings, 'restart')
        self.csgo500_restart_store_global_time = self.get_key(self.csgo500_settings_restart, 'restart store global time')
        self.csgo500_restart_server_validity_time = self.get_key(self.csgo500_settings_restart, 'restart server validity time')
        self.csgo500_restart_server_global_time = self.get_key(self.csgo500_settings_restart, 'restart server global time')
        self.csgo500_restart_bots_name = self.get_key(self.csgo500_settings_restart, 'restart bots name')  # list of dict
        self.csgo500_restart_bots_global_time = self.get_key(self.csgo500_settings_restart, 'restart bots global time')
        # endregion

        # region Collection shadowpay_seller_settings
        self.shadowpay_settings_telegram = self.get_key(self.content_shadowpay_settings, 'telegram')
        self.shadowpay_tg_token = self.get_key(self.shadowpay_settings_telegram, 'tg token')
        self.shadowpay_tg_id = self.get_key(self.shadowpay_settings_telegram, 'tg id')
        self.shadowpay_tg_bot_name = self.get_key(self.shadowpay_settings_telegram, 'tg bot name')

        self.shadowpay_settings_general = self.get_key(self.content_shadowpay_settings, 'general')
        self.shadowpay_waiting_start_time = self.get_key(self.shadowpay_settings_general, 'waiting start time')
        self.shadowpay_thread_start_time = self.get_key(self.shadowpay_settings_general, 'thread start time')
        self.shadowpay_thread_function_time = self.get_key(self.shadowpay_settings_general, 'thread function time')
        self.shadowpay_url = f"https://{self.get_key(self.shadowpay_settings_general, 'url')}"
        self.shadowpay_site_apikey_global_time = self.get_key(self.shadowpay_settings_general, 'site apikey global time')
        self.shadowpay_balance_transfer_global_time = self.get_key(self.shadowpay_settings_general, 'balance transfer global time')
        self.shadowpay_sale_price_bot_name = self.get_key(self.shadowpay_settings_general, 'sale price bot name')

        self.shadowpay_settings_online = self.get_key(self.content_shadowpay_settings, 'online')
        self.shadowpay_ping_global_time = self.get_key(self.shadowpay_settings_online, 'ping global time')
        self.shadowpay_visible_store_max_number_of_inv_items = self.get_key(self.shadowpay_settings_online, 'visible store max number of inv items')
        self.shadowpay_visible_store_global_time = self.get_key(self.shadowpay_settings_online, 'visible store global time')

        self.shadowpay_settings_items = self.get_key(self.content_shadowpay_settings, 'items')
        self.shadowpay_add_to_sale_global_time = self.get_key(self.shadowpay_settings_items, 'add to sale global time')
        self.shadowpay_change_price_global_time = self.get_key(self.shadowpay_settings_items, 'change price global time')

        self.shadowpay_settings_steam = self.get_key(self.content_shadowpay_settings, 'steam')
        self.shadowpay_steam_send_offers_global_time = self.get_key(self.shadowpay_settings_steam, 'steam send offers global time')
        self.shadowpay_steam_cancel_offers_sites_name = self.get_key(self.shadowpay_settings_steam, 'steam cancel offers sites name')  # list of dict
        self.shadowpay_steam_cancel_offers_global_time = self.get_key(self.shadowpay_settings_steam, 'steam cancel offers global time')

        self.shadowpay_settings_history = self.get_key(self.content_shadowpay_settings, 'history')
        self.shadowpay_history_tg_token = self.get_key(self.shadowpay_settings_history, 'history tg token')
        self.shadowpay_history_tg_id = self.get_key(self.shadowpay_settings_history, 'history tg id')
        self.shadowpay_history_global_time = self.get_key(self.shadowpay_settings_history, 'history global time')

        self.shadowpay_settings_restart = self.get_key(self.content_shadowpay_settings, 'restart')
        self.shadowpay_restart_store_global_time = self.get_key(self.shadowpay_settings_restart, 'restart store global time')
        self.shadowpay_restart_server_validity_time = self.get_key(self.shadowpay_settings_restart, 'restart server validity time')
        self.shadowpay_restart_server_global_time = self.get_key(self.shadowpay_settings_restart, 'restart server global time')
        self.shadowpay_restart_bots_name = self.get_key(self.shadowpay_settings_restart, 'restart bots name')  # list of dict
        self.shadowpay_restart_bots_global_time = self.get_key(self.shadowpay_settings_restart, 'restart bots global time')
        # endregion

        # region Collection buff_seller_settings
        self.buff_settings_telegram = self.get_key(self.content_buff_settings, 'telegram')
        self.buff_tg_token = self.get_key(self.buff_settings_telegram, 'tg token')
        self.buff_tg_id = self.get_key(self.buff_settings_telegram, 'tg id')
        self.buff_tg_bot_name = self.get_key(self.buff_settings_telegram, 'tg bot name')

        self.buff_settings_general = self.get_key(self.content_buff_settings, 'general')
        self.buff_waiting_start_time = self.get_key(self.buff_settings_general, 'waiting start time')
        self.buff_thread_start_time = self.get_key(self.buff_settings_general, 'thread start time')
        self.buff_thread_function_time = self.get_key(self.buff_settings_general, 'thread function time')
        self.buff_url = f"https://{self.get_key(self.buff_settings_general, 'url')}"
        self.buff_site_apikey_global_time = self.get_key(self.buff_settings_general, 'site apikey global time')
        self.buff_balance_transfer_global_time = self.get_key(self.buff_settings_general, 'balance transfer global time')
        self.buff_sale_price_bot_name = self.get_key(self.buff_settings_general, 'sale price bot name')

        self.buff_settings_online = self.get_key(self.content_buff_settings, 'online')
        self.buff_ping_global_time = self.get_key(self.buff_settings_online, 'ping global time')
        self.buff_visible_store_max_number_of_inv_items = self.get_key(self.buff_settings_online, 'visible store max number of inv items')
        self.buff_visible_store_global_time = self.get_key(self.buff_settings_online, 'visible store global time')

        self.buff_settings_items = self.get_key(self.content_buff_settings, 'items')
        self.buff_add_to_sale_global_time = self.get_key(self.buff_settings_items, 'add to sale global time')
        self.buff_change_price_global_time = self.get_key(self.buff_settings_items, 'change price global time')

        self.buff_settings_steam = self.get_key(self.content_buff_settings, 'steam')
        self.buff_steam_send_offers_global_time = self.get_key(self.buff_settings_steam, 'steam send offers global time')
        self.buff_steam_cancel_offers_sites_name = self.get_key(self.buff_settings_steam, 'steam cancel offers sites name')  # list of dict
        self.buff_steam_cancel_offers_global_time = self.get_key(self.buff_settings_steam, 'steam cancel offers global time')

        self.buff_settings_history = self.get_key(self.content_buff_settings, 'history')
        self.buff_history_tg_token = self.get_key(self.buff_settings_history, 'history tg token')
        self.buff_history_tg_id = self.get_key(self.buff_settings_history, 'history tg id')
        self.buff_history_global_time = self.get_key(self.buff_settings_history, 'history global time')

        self.buff_settings_restart = self.get_key(self.content_buff_settings, 'restart')
        self.buff_restart_store_global_time = self.get_key(self.buff_settings_restart, 'restart store global time')
        self.buff_restart_server_validity_time = self.get_key(self.buff_settings_restart, 'restart server validity time')
        self.buff_restart_server_global_time = self.get_key(self.buff_settings_restart, 'restart server global time')
        self.buff_restart_bots_name = self.get_key(self.buff_settings_restart, 'restart bots name')  # list of dict
        self.buff_restart_bots_global_time = self.get_key(self.buff_settings_restart, 'restart bots global time')
        # endregion

        # region Telegram Info
        self.sellpy_tg_info = main_tg_info

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

        if self.waxpeer_tg_token:
            self.waxpeer_tg_bot = telebot.TeleBot(self.waxpeer_tg_token)
        self.waxpeer_tg_info = {
            'tg id': self.waxpeer_tg_id,
            'tg bot': self.waxpeer_tg_bot,
            'bot name': self.waxpeer_tg_bot_name
        }

        if self.waxpeer_history_tg_token:
            self.waxpeer_history_tg_bot = telebot.TeleBot(self.waxpeer_history_tg_token)
        self.waxpeer_history_tg_info = {
            'tg id': self.waxpeer_history_tg_id,
            'tg bot': self.waxpeer_history_tg_bot,
            'bot name': self.waxpeer_tg_bot_name
        }

        if self.csgoempire_tg_token:
            self.csgoempire_tg_bot = telebot.TeleBot(self.csgoempire_tg_token)
        self.csgoempire_tg_info = {
            'tg id': self.csgoempire_tg_id,
            'tg bot': self.csgoempire_tg_bot,
            'bot name': self.csgoempire_tg_bot_name
        }

        if self.csgoempire_history_tg_token:
            self.csgoempire_history_tg_bot = telebot.TeleBot(self.csgoempire_history_tg_token)
        self.csgoempire_history_tg_info = {
            'tg id': self.csgoempire_history_tg_id,
            'tg bot': self.csgoempire_history_tg_bot,
            'bot name': self.csgoempire_tg_bot_name
        }

        if self.csgo500_tg_token:
            self.csgo500_tg_bot = telebot.TeleBot(self.csgo500_tg_token)
        self.csgo500_tg_info = {
            'tg id': self.csgo500_tg_id,
            'tg bot': self.csgo500_tg_bot,
            'bot name': self.csgo500_tg_bot_name
        }

        if self.csgo500_history_tg_token:
            self.csgo500_history_tg_bot = telebot.TeleBot(self.csgo500_history_tg_token)
        self.csgo500_history_tg_info = {
            'tg id': self.csgo500_history_tg_id,
            'tg bot': self.csgo500_history_tg_bot,
            'bot name': self.csgo500_tg_bot_name
        }

        if self.shadowpay_tg_token:
            self.shadowpay_tg_bot = telebot.TeleBot(self.shadowpay_tg_token)
        self.shadowpay_tg_info = {
            'tg id': self.shadowpay_tg_id,
            'tg bot': self.shadowpay_tg_bot,
            'bot name': self.shadowpay_tg_bot_name
        }

        if self.shadowpay_history_tg_token:
            self.shadowpay_history_tg_bot = telebot.TeleBot(self.shadowpay_history_tg_token)
        self.shadowpay_history_tg_info = {
            'tg id': self.shadowpay_history_tg_id,
            'tg bot': self.shadowpay_history_tg_bot,
            'bot name': self.shadowpay_tg_bot_name
        }

        if self.buff_tg_token:
            self.buff_tg_bot = telebot.TeleBot(self.buff_tg_token)
        self.buff_tg_info = {
            'tg id': self.buff_tg_id,
            'tg bot': self.buff_tg_bot,
            'bot name': self.buff_tg_bot_name
        }

        if self.buff_history_tg_token:
            self.buff_history_tg_bot = telebot.TeleBot(self.buff_history_tg_token)
        self.buff_history_tg_info = {
            'tg id': self.buff_history_tg_id,
            'tg bot': self.buff_history_tg_bot,
            'bot name': self.buff_tg_bot_name
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

    def update_db_prices_and_settings(self):
        try:
            database_prices = self.get_first_doc_from_mongo_collection(self.database_prices_collection)
            if database_prices:
                self.content_database_prices = database_prices
            database_settings = self.get_first_doc_from_mongo_collection(self.database_settings_collection)
            if database_settings:
                self.content_database_settings = database_settings
        except:
            pass
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
            Logs.notify_except(self.sellpy_tg_info, f"MongoDB: Error while creating Merge Info for Parsing: {e}", '')
        return result

    def search_in_merges_by_username(self, tg_info, username):
        try:
            for sublist in self.content_merges:
                if sublist[0]['username'] == username:
                    return sublist[1]
        except Exception as e:
            Logs.notify_except(tg_info, f"MongoDB: Error searching in Merges Info by username: {e}", '')
        return None
    # endregion


    # region Price Info
    def get_information_for_price(self, tg_info, name_of_seller):
        try:
            database_setting_bots = self.content_database_settings['DataBaseSettings']['Sellers_SalePrice']['bots']
            seller_value = None
            for key, value in database_setting_bots.items():
                if name_of_seller in key:
                    seller_value = value
                    break
            return seller_value
        except Exception as e:
            Logs.notify_except(tg_info, f"MongoDB: Error during receiving Sellers_SalePrice: {e}", '')
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
                    Logs.notify(self.sellpy_tg_info, f"MongoDB: Key '{key}' not found in {dictionary}", '')
        except:
            pass
        return None
    # endregion
