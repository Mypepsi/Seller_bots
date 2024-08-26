import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.steampy.client import Asset
from bots_libraries.steampy.models import GameOptions
from bots_libraries.sellpy.steam import Steam


class CSGOEmpireSteam(Steam):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)