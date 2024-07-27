from datetime import datetime
import os
import sys
import traceback
import inspect


class Logs:
    @staticmethod
    def get_tg_dict_info(result, tg_bot_dict, text, user_name, exception: bool):
        tg_id = tg_bot_dict['tg id']
        tg_bot = tg_bot_dict['tg bot']
        sellers_name = tg_bot_dict['bot name']
        try:
            tg_bot.send_message(tg_id, )
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
                  'file name': file_name,
                  'directory name': directory_name,
                  'error line number': line_number}
        return result

    @staticmethod
    def notify_log(text, user_name):
        try:
            r = Logs.get_except_info()
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
    def except_log(text, user_name):
        try:
            r = Logs.get_except_info()
            if user_name == '':
                log_message = (f"[{r['time stamp']}] [{r['directory name']}] [{r['file name']}:"
                               f"{r['error line number']}]: {text}")

            else:
                log_message = (f"[{r['time stamp']}] [{r['directory name']}] [{r['file name']}:"
                               f"{r['error line number']}]: {user_name}]: {text}")
            print(log_message)
        except:
            pass

    @staticmethod
    def notify_log_and_tg_msg(tg_bot_dict, text, user_name):
        usual_result = Logs.get_except_info()
        Logs.get_tg_dict_info(usual_result, tg_bot_dict, text, user_name, False)

    @staticmethod
    def except_log_and_tg_msg(tg_bot_dict, text, user_name):
        except_result = Logs.get_except_info()
        Logs.get_tg_dict_info(except_result, tg_bot_dict, text, user_name, True)

    @staticmethod
    def send_msg_in_tg(tg_bot_dict, func_name, username):
        tg_id = tg_bot_dict['tg id']
        tg_bot = tg_bot_dict['tg bot']
        sellers_name = tg_bot_dict['bot name']
        try:
            tg_bot.send_message(tg_id, f'{sellers_name}: {func_name}: {username}')
        except:
            pass

    @staticmethod
    def log_and_send_msg_in_tg(tg_bot_dict, func_name_and_info, username):
        tg_id = tg_bot_dict['tg id']
        tg_bot = tg_bot_dict['tg bot']
        sellers_name = tg_bot_dict['bot name']
        try:
            now = datetime.now()
            tg_bot.send_message(tg_id, f'{sellers_name}: {func_name_and_info}: {username}')
            print(f'[{now.strftime("%d-%m-%Y %H:%M:%S")}]: {username}: {func_name_and_info}')
        except:
            pass


class ExitException(Exception):
    pass