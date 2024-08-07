import os
import sys
import time
import inspect
import traceback
from datetime import datetime
from pymongo import MongoClient


class Logs:
    # region Send Info
    @staticmethod
    def log(text, username):
        try:
            now = datetime.now()
            date = now.strftime("%d.%m.%Y %H:%M:%S")
            log_message = f'[{date}]'
            if username:
                log_message += f' [{username}]'
            log_message += f': {text}'
            print(log_message)
        except:
            pass

    @staticmethod
    def notify(tg_bot_dict, text, username):
        try:
            sellers_name = tg_bot_dict['bot name']
            Logs.log(text, username)
            r = Logs.get_logs_info(False, username)
            tg_message = f"[{sellers_name}] [{r['file name']}: {r['line number']}] "
            if username:
                tg_message += f'[{username}]'
            else:
                tg_message += f"[{r['ip address']}]"
            tg_message += f':\n{text}'
            tg_bot_dict['tg bot'].send_message(tg_bot_dict['tg id'], tg_message, timeout=5)
        except:
            pass
        time.sleep(3)
    #endregion


    # region Send Info Except
    @staticmethod
    def log_except(text, username, info=None):
        try:
            if not info:
                r = Logs.get_logs_info(True, True)
            else:
                r = info
            log_message = f"[{r['date']}] [traceback: {r['file name']}: {r['line number']}]"
            if username:
                log_message += f' [{username}]'
            log_message += f':\n{text}'
            print(log_message)
        except:
            pass

    @staticmethod
    def notify_except(tg_bot_dict, text, username):
        try:
            sellers_name = tg_bot_dict['bot name']
            r = Logs.get_logs_info(True, username)
            Logs.log_except(text, username, info=r)
            tg_message = f"[{sellers_name}] [traceback: {r['file name']}: {r['line number']}] "
            if username:
                tg_message += f'[{username}]'
            else:
                tg_message += f"[{r['ip address']}]"
            tg_message += f':\n{text}'
            tg_bot_dict['tg bot'].send_message(tg_bot_dict['tg id'], tg_message, timeout=5)
        except:
            pass
        time.sleep(3)
    #endregion


    @staticmethod
    def get_logs_info(except_bool: bool, username):
        try:
            now = datetime.now()
            date = now.strftime("%d.%m.%Y %H:%M:%S")
        except:
            date = 'Time not found'

        file_name = 'File not found'
        line_number = 0
        try:
            if except_bool:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                last_frame = traceback.extract_tb(exc_traceback)[-1]
                file_name = os.path.basename(last_frame.filename)
                line_number = last_frame.lineno
            else:
                stack = inspect.stack()
                frame = stack[2]
                file_path = frame.filename
                file_name = os.path.basename(file_path)
                line_number = frame.lineno
        except:
            pass

        ip_address = 'IP not found'
        try:
            if not username:
                client = MongoClient(
                    "mongodb://127.0.0.1:27017",
                    serverSelectionTimeoutMS=30000,  # Server selection timeout.
                    connectTimeoutMS=30000,  # Connection timeout.
                    socketTimeoutMS=30000,  # Read/write timeout.
                    wtimeoutMS=30000,  # Write acknowledgment timeout.
                    minPoolSize=0,  # Minimum connections in pool.
                    maxPoolSize=10  # Maximum connections in pool.
                )
                db_client = client['Seller_DataBases']
                collection_name = db_client['database_ip']
                doc_ip_address = collection_name.find_one()
                ip_address = doc_ip_address['ip_address']
                client.close()
        except:
            pass

        result = {'date': date,
                  'file name': file_name,
                  'line number': line_number,
                  'ip address': ip_address}
        return result

class ExitException(Exception):
    pass