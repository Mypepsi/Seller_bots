from datetime import datetime


class Logs:
    @staticmethod
    def log(text):
        now = datetime.now()
        print(f'[{now.strftime("%d-%m-%Y %H:%M:%S")}]: {text}')
