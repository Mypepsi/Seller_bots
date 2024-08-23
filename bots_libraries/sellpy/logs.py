import os
import sys
import time
import socket
import inspect
import traceback
from datetime import datetime


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
            r = Logs.get_logs_info(False, username)
            Logs.log(text, username)
            sellers_name = tg_bot_dict['bot name']
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
            r = Logs.get_logs_info(True, username)
            Logs.log_except(text, username, info=r)
            sellers_name = tg_bot_dict['bot name']
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

    # region Get Info
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
                second_frame = stack[2]
                file_name = os.path.basename(second_frame.filename)
                line_number = second_frame.lineno
        except:
            pass

        ip_address = 'IP not found'
        if not username:
            server_ip = Logs.get_server_ip()
            if server_ip:
                ip_address = server_ip

        result = {'date': date,
                  'file name': file_name,
                  'line number': line_number,
                  'ip address': ip_address}
        return result

    @staticmethod
    def get_server_ip():
        ip_address = None
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(0)
            s.connect(('8.8.8.8', 1))
            ip_address = s.getsockname()[0]
        except:
            pass
        finally:
            s.close()
        return ip_address


    @staticmethod
    def get_bot_name():
        bot_name = 'Bot  not found'
        try:
            stack = inspect.stack()
            last_frame = stack[-1]
            bot_name = os.path.splitext(os.path.basename(last_frame.filename))[0].replace("_", " ")
        except:
            pass

        return bot_name
    #endregion




class ExitException(Exception):
    pass