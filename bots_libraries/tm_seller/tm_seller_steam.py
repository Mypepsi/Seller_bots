from bots_libraries.information.logs import Logs
from bots_libraries.information.mongo import Mongo
from bots_libraries.creator.creator_steam import Steam
from bots_libraries.steampy.confirmation import ConfirmationExecutor
from bots_libraries.steampy.confirmation import Confirmation
from bots_libraries.steampy.models import GameOptions
from bots_libraries.steampy.client import Asset
from lxml import html
from fake_useragent import UserAgent
import string
import pickle
import json
import io
import random
import time
import traceback
import requests


class TMSteam(Steam):
    def __init__(self):
        super().__init__()

    def tm_trades(self, acc_info, time_sleep):
        username = ''
        while True:
            self.update_account_data_info()
            try:
                username = acc_info['username']
                steam_session = acc_info['steam session']
                self.take_session(steam_session)
                url = f'https://market.csgo.com/api/v2/trade-request-give-p2p-all?key={self.steamclient.tm_api}'
                response = requests.get(url, timeout=10)
                response_data = response.json()
                break
            except Exception:
                time.sleep(5)

        #self.logs.write_log(self.tm_logs_path, 'tm_trades', f'Вещи, которые необходимо отправить загружены.')
        # если есть трейды - проверяем список уже отправленных трейдов и удаляем уже отправленные трейды
        if 'offers' in response_data and type(response_data['offers']) == list:
            sent_offers = SDA.get_tm_sent_offers() #csgo_tm_sent_offers
            # подтвержденные трейды
            sent_trade_ready = SDA.get_tm_sent_offers_ready()  #csgo_tm_sent_trade_ready

            # проверка трейдов которые не подтверждены через апи тма
            # дістаєм трейд з документа
            for offer in sent_offers:
                try:
                    data = json.loads(offer)
                except:
                    continue

                trade_id = data['trade_id']
                data_text = data['text']

                if str(trade_id) in sent_trade_ready:
                    continue #до кінця цього кола у циклі фор нічого не робиться

                # ищем текст в ответе от тма
                for i in range(len(response_data['offers'])):
                    msg = response_data['offers'][i]['tradeoffermessage']
                    if msg == data_text:
                        # нужно подтвердить трейд через trade_ready

                        try:
                            url = f'https://market.csgo.com/api/v2/trade-ready?key={self.steamclient.tm_api}&tradeoffer={trade_id}'
                            response_ = requests.get(url, timeout=10)
                            response_data_ = response_.json()
                        except Exception:
                            break

                        if 'success' in response_data_ and response_data_['success']:
                            # запись в подтвержденные трейды
                            Bot.file_with_lock(
                                file_path=SDA.SENT_OFFERS_READY_TRADE,
                                file_mode='a',
                                text_to_write=f'{json.dumps({"trade_id": trade_id})}\n'
                            )

                        break
                    else:
                        continue

            new_sent_offers = {}
            for offer in sent_offers:
                try:
                    data = json.loads(offer)
                except:
                    continue

                if data['text'] not in new_sent_offers:
                    new_sent_offers.update({data['text']: {"trade_id": data['trade_id'], "asset_id": data['trade_id']}})
                else:
                    new_sent_offers[data['text']]["trade_id"] = data['trade_id']

            count_to_sent = 0
            for i in range(len(response_data['offers'])):

                msg = response_data['offers'][i]['tradeoffermessage']
                if msg in new_sent_offers:
                    # проверка трейда по апи стима
                    trade_id = new_sent_offers[msg]['trade_id']
                    response_ = self.steamclient.get_trade_offer_state(trade_id)

                    if not isinstance(response_data_, dict):
                        continue

                    if 'response' in response_data_ and 'offer' in response_data_['response']:
                        offer_state = response_data_['response']['offer']['trade_offer_state']
                    else:
                        continue

                    if int(offer_state) not in [1, 4, 8, 10]:
                        continue

                # проверка сообщений в отправленных трейдах

                count_to_sent += 1

                asset_list = []
                asset_list_for_cancel = []
                for as_ in response_data['offers'][i]['items']:
                    asset_id = as_['assetid']
                    my_asset = Asset(str(asset_id), GameOptions.CS)
                    asset_list_for_cancel.append(str(asset_id))
                    asset_list.append(my_asset)

                partner = response_data['offers'][i]['partner']
                token = response_data['offers'][i]['token']
                trade_offer_url = f'https://steamcommunity.com/tradeoffer/new/?partner={partner}&token={token}'

                self.logs.write_log('', 'tm_trades', extra_text=f'Необходимо отправить и подтвердить: {[asset_list_for_cancel, trade_offer_url]}')
                while True:
                    try:
                        steam_response = self.steamclient.make_offer_with_url(asset_list, [], trade_offer_url, '')
                        time.sleep(3)
                        if 'tradeofferid' in steam_response:
                            string = json.dumps({
                                "text": msg,
                                "asset_id": asset_list_for_cancel,
                                "platform": 'tm',
                                "trade_id": steam_response['tradeofferid'],
                                "sent_time": int(time.time()),
                            })


                            Bot.file_with_lock(
                                'data/sda/cancel_active_send_offers.txt',
                                'a',
                                text_to_write=f'{string}\n'
                            )


                            self.logs.write_log(SDA.log_path, 'Обмен на ТМ успешно отправлен.')
                            string = json.dumps({"text": msg, "asset_id": asset_list_for_cancel, "trade_id": steam_response['tradeofferid']})
                            SDA.add_tm_sent_offers(string)
                        else:
                            self.logs.write_log(SDA.log_path, 'ошибка при отправке предмета')
                            self.logs.write_log(SDA.log_path, f'{steam_response}')
                        break
                    except Exception:
                        error = str(traceback.format_exc())
                        print(error)
                        self.logs.write_log(SDA.log_path, 'ошибка при отправка трейда стим')
                        self.logs.write_log(SDA.log_path, error)
                        time.sleep(5)

            if count_to_sent == 0:
                self.logs.write_log(self.tm_logs_path, 'tm_trades', f'Ничего не нужно передавать.')
        elif 'error' in response_data:
            if response_data['error'] == 'nothing':
                self.logs.write_log(self.tm_logs_path, 'tm_trades', f'Ничего не нужно передавать.')


















