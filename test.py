from datetime import datetime, timedelta
import requests

end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

history_url = (f'https://api.shadowpay.com/api/v2/user/operations?token=f2a0f8809feda2b10fcd9d314d8d6692'
               f'&type=sell&date_from={start_date}&date_to={end_date}&limit=1000&offset=0'
               f'&sort_column=time_created&sort_dir=desc')
response = requests.get(history_url, timeout=15).json()

print(response)
