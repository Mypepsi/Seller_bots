from bots_libraries.tm_seller.tm_seller_steam import TMSteam
from bots_libraries.steampy.client import SteamClient

import itertools
import requests
import urllib.parse


class Test(TMSteam):
    def __init__(self):
        super().__init__()
        self.steamclient = SteamClient('')
        self.steamclient.tm_api = '27FzU90g6Mc0zD1BDpaU934H6gX62UQ'
        
    def test(self):
        acc_data_tradable_inventory = {
        "38325265554" : {
            "asset_id" : "38325265554",
            "market_hash_name" : "Glock-18 | Oxide Blaze (Factory New)",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38320447057" : {
            "asset_id" : "38320447057",
            "market_hash_name" : "Music Kit | Austin Wintory, Bachram",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38304238972" : {
            "asset_id" : "38304238972",
            "market_hash_name" : "Seal Team 6 Soldier | NSWC SEAL",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38297574833" : {
            "asset_id" : "38297574833",
            "market_hash_name" : "Dragomir | Sabre",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38296957569" : {
            "asset_id" : "38296957569",
            "market_hash_name" : "Seal Team 6 Soldier | NSWC SEAL",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38274906004" : {
            "asset_id" : "38274906004",
            "market_hash_name" : "MP5-SD | Nitro (Field-Tested)",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38232856274" : {
            "asset_id" : "38232856274",
            "market_hash_name" : "StatTrak™ MP9 | Hydra (Minimal Wear)",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38230400418" : {
            "asset_id" : "38230400418",
            "market_hash_name" : "Markus Delrow | FBI HRT",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38228603437" : {
            "asset_id" : "38228603437",
            "market_hash_name" : "StatTrak™ USP-S | Ticket to Hell (Battle-Scarred)",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38202727118" : {
            "asset_id" : "38202727118",
            "market_hash_name" : "MP9 | Starlight Protector (Battle-Scarred)",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38201535144" : {
            "asset_id" : "38201535144",
            "market_hash_name" : "Lieutenant Rex Krikey | SEAL Frogman",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38197010207" : {
            "asset_id" : "38197010207",
            "market_hash_name" : "M4A4 | Evil Daimyo (Factory New)",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38175174008" : {
            "asset_id" : "38175174008",
            "market_hash_name" : "'Two Times' McCoy | TACP Cavalry",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38166801244" : {
            "asset_id" : "38166801244",
            "market_hash_name" : "MP9 | Mount Fuji (Minimal Wear)",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38123023684" : {
            "asset_id" : "38123023684",
            "market_hash_name" : "StatTrak™ M4A4 | Magnesium (Minimal Wear)",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        },
        "38092953952" : {
            "asset_id" : "38092953952",
            "market_hash_name" : "Galil AR | Chromatic Aberration (Minimal Wear)",
            "launch_price" : 0.0,
            "service_launch_price" : "None",
            "time" : 1719490900
        }
    }
        store_items = self.get_store_items()
        print(store_items)
        if 'items' in store_items and type(store_items['items']) == list:
            tm_api_for_parsing = [item["tm apikey"] for item in self.content_acc_for_parsing_list]
            print(tm_api_for_parsing)
            unique_iterator = itertools.cycle(tm_api_for_parsing)
            for i in range(len(acc_data_tradable_inventory)):
                item_name = acc_data_tradable_inventory['38325265554']['market_hash_name']
                print(item_name)
                coded_item_name = urllib.parse.quote(item_name)
                unique_tm_api = next(unique_iterator)
        
                search_hash_name_url = (f'https://market.csgo.com/api/v2/search-list-items-by-hash-name-all?'
                                        f'key={unique_tm_api}&extended=1&list_hash_name[]={coded_item_name}')
        
                parsed_info = requests.get(search_hash_name_url, timeout=10).json()
                print(parsed_info)
                item_prices = [item["price"] for item in parsed_info['data'][item_name]]
                print(item_prices)
                min_value = min([int(price) for price in item_prices])
                print(min_value)
                tm_seller_value = self.taking_tm_information_for_pricing()

                max_market_price = self.get_my_market_price(
                    acc_data_tradable_inventory['38325265554'], tm_seller_value, 'max')
        
                min_market_price = self.get_my_market_price(
                    acc_data_tradable_inventory['38325265554'], tm_seller_value, 'min')
                
                print(max_market_price)
                print(min_market_price)


test = Test()
test.test()
