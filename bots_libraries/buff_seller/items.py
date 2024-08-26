import time
import requests
import threading
import urllib.parse
from queue import Queue, Empty
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.steam import Steam


class BuffItems(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)