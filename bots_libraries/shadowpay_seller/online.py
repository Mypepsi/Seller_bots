import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam_manager import SteamManager
from bots_libraries.sellpy.logs import Logs, ExitException


class ShadowPayOnline(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)