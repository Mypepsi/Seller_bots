from datetime import datetime
import time

trades = [
            {
                "created": "2024-09-29T14:53:23.476Z",
                "date": "2024-09-29T16:13:57.848Z",
                "id": 16391036,
                "item_id": "38742285055",
                "give_amount": 5000,
                "image": "https://steamcommunity-a.akamaihd.net/economy/image/class/730/4141779083/200fx125f",
                "price": 5000,
                "game": "csgo",
                "name": "MP5-SD | Nitro (Field-Tested)",
                "market_name": "Nitro",
                "status": 6,
                "average": 7130,
                "action": "sell"
            },
            {
                "created": "2024-08-26T16:57:35.234Z",
                "date": "2024-08-26T16:58:32.003Z",
                "id": 15491333,
                "item_id": "38794226842",
                "give_amount": 6580,
                "image": "https://steamcommunity-a.akamaihd.net/economy/image/class/730/6058183065/200fx125f",
                "price": 6580,
                "game": "csgo",
                "name": "StatTrak™ Sawed-Off | Devourer (Field-Tested)",
                "market_name": "Devourer",
                "status": 5,
                "average": 9690,
                "action": "sell"
            },
            {
                "created": "2024-08-26T16:56:55.752Z",
                "date": "2024-08-26T16:57:22.119Z",
                "id": 15491320,
                "item_id": "38794226781",
                "give_amount": 6580,
                "image": "https://steamcommunity-a.akamaihd.net/economy/image/class/730/6058183065/200fx125f",
                "price": 6580,
                "game": "csgo",
                "name": "StatTrak™ Sawed-Off | Devourer (Field-Tested)",
                "market_name": "Devourer",
                "status": 5,
                "average": 9690,
                "action": "sell"
            }]

for trade in trades:
    trade["created"] = int(time.mktime(datetime.strptime(trade["created"], "%Y-%m-%dT%H:%M:%S.%fZ").timetuple()))


print(trades)
