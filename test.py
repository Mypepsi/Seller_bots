import requests

payload = {
  "name": [
    "AK-47 | Redline (Field-Tested)"
  ],
  "sell": 1
}
get_inventory_url = (f'https://api.waxpeer.com/v1/check-availability?api=0f6940ee662259d75538a0b0b028ddb9e5a75b8ee2a6617882d2854def8ad388&item_id=37376517712')


response = requests.get(get_inventory_url).json()
print(response)
# print(len(response['data']['AK-47 | Redline (Field-Tested)']['listings']))
