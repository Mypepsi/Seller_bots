import time
import random
import requests
import urllib.parse
from bots_libraries.sellpy.logs import Logs, ExitException
from bots_libraries.sellpy.thread_manager import ThreadManager


class WaxpeerOnline(ThreadManager):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)