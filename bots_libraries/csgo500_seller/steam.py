import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.steampy.client import Asset
from bots_libraries.steampy.models import GameOptions


class CSGO500Steam(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)