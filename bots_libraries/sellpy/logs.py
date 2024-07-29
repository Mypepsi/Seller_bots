from datetime import datetime
import os
import sys
import socket
import inspect
import traceback

class Logs:
    #region main
    @staticmethod
    def log(text, user_name):
        try:
            r = Logs.get_usual_info()
            if user_name == '':
                log_message = f"[{r['time stamp']}] [{r['directory name']}] [{r['file name']}:{r['line number']}]: {text}"
            else:
                log_message = (
                    f"[{r['time stamp']}] [{r['directory name']}] [{r['file name']}:{r['line number']}]: "
                    f"{user_name}]: {text}")
            print(log_message)
        except:
            pass

    @staticmethod
    def log_except(text, user_name):
        try:
            r = Logs.get_except_info()
            log_message = f"[{r['time stamp']}] [{r['directory name']}] [{r['file name']}:{r['line number']}]:"

            if user_name:
                log_message += f" {user_name}:"

            log_message += f" {text}"
            print(log_message)
        except:
            pass

    @staticmethod
    def notify(tg_bot_dict, text, user_name):
        Logs.log_and_send_tg_msg(tg_bot_dict, text, user_name, False)

    @staticmethod
    def notify_except(tg_bot_dict, text, user_name):
        Logs.log_and_send_tg_msg(tg_bot_dict, text, user_name, True)
    #endregion

    #region secondary
    @staticmethod
    def log_and_send_tg_msg(tg_bot_dict, text, user_name, exception: bool):
        tg_id = tg_bot_dict['tg id']
        tg_bot = tg_bot_dict['tg bot']
        sellers_name = tg_bot_dict['bot name']
        if exception:
            r = Logs.get_except_info()
        else:
            r = Logs.get_usual_info()
        if user_name == '':
            ip = Logs.get_ip_address()
            if sellers_name:
                log_message = (f"[{r['time stamp']}] [{sellers_name}] [{r['file name']}:{r['line number']}]:"
                               f" {text}")
                tg_message = (f"[{r['time stamp']}] [{sellers_name}] [{r['file name']}:{r['line number']}]: [{ip}]:"
                              f"\n{text}")
            else:
                log_message = (f"[{r['time stamp']}] [{r['file name']}:{r['line number']}]:"
                               f" {text}")
                tg_message = (f"[{r['time stamp']}] [{r['file name']}:{r['line number']}]: [{ip}]:"
                              f"\n{text}")
        else:
            if sellers_name:
                log_message = (
                    f"[{r['time stamp']}] [{sellers_name}] [{r['file name']}:{r['line number']}]: "
                    f"[{user_name}]: {text}")
                tg_message = (f"[{r['time stamp']}] [{sellers_name}] [{r['file name']}:{r['line number']}]: "
                              f"[{user_name}]:\n{text}")
            else:
                log_message = (f"[{r['time stamp']}] [{r['file name']}:{r['line number']}]:"
                               f" {text}")
                tg_message = (f"[{r['time stamp']}] [{r['file name']}:{r['line number']}]: [{user_name}]:"
                              f"\n{text}")

        print(log_message)
        try:
            tg_bot.send_message(tg_id, tg_message, timeout=5)
        except:
            pass

    @staticmethod
    def get_usual_info():
        try:
            now = datetime.now()
            time_stamp = now.strftime("%d-%m-%Y %H:%M:%S")
        except:
            time_stamp = None
        try:
            stack = inspect.stack()
            frame = stack[1]
            file_path = frame.filename
            file_name = os.path.basename(file_path)
        except:
            frame = None
            file_path = None
            file_name = None
        try:
            directory_name = os.path.basename(os.path.dirname(file_path))
        except:
            directory_name = None
        try:
            line_number = frame.lineno
        except:
            line_number = None
        result = {'time stamp': time_stamp,
                  'file name': file_name,
                  'directory name': directory_name,
                  'line number': line_number}
        return result

    @staticmethod
    def get_except_info():
        try:
            now = datetime.now()
            time_stamp = now.strftime("%d-%m-%Y %H:%M:%S")
        except:
            time_stamp = None
        try:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            last_frame = traceback.extract_tb(exc_traceback)[-1]
        except:
            last_frame = None
        try:
            file_name = os.path.basename(last_frame.filename)
        except:
            file_name = None
        try:
            directory_name = os.path.basename(os.path.dirname(last_frame.filename))
        except:
            directory_name = None
        try:
            line_number = last_frame.lineno
        except:
            line_number = None
        result = {'time stamp': time_stamp,
                  'file name': f'traсeback: {file_name}',
                  'directory name': directory_name,
                  'line number': line_number}
        return result

    @staticmethod
    def get_ip_address():
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            s.connect(('8.8.8.8', 1))
            ip_address = s.getsockname()[0]
        except:
            ip_address = 'IP not found'
        finally:
            s.close()
        return ip_address
    #endregion


class ExitException(Exception):
    pass