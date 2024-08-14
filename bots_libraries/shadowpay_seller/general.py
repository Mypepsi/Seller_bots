import time
import requests
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.thread_manager import ThreadManager


class ShadowPayGeneral(ThreadManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)