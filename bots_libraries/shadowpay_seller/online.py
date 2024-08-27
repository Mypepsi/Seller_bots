import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.steam import Steam
from bots_libraries.sellpy.logs import Logs, ExitException


class ShadowPayOnline(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)