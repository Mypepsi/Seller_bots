import time
import requests
import threading
import urllib.parse
from queue import Queue, Empty
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam_manager import SteamManager


class ShadowPayItems(SteamManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)