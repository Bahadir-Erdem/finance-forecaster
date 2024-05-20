from datetime import datetime
from pytz import timezone
import requests
import json
import pandas as pd

# class Timezone: eklenebilir
#     def __init__(self, zone: str) -> None:
#         self.zone = zone

#     def get_zone(self):
#         return self.zone
    
class Date:
    def __init__(self):
        self.default_timezone = timezone('Turkey')
        self.now = datetime.now(self.default_timezone)

    def get_current_quarter(self):
        return (self.now.month - 1) // 3 + 1

    def get_current_date(self):
        return {
            'date' : self.now.date(),
            'day' : self.now.day,
            'week' : self.now.isocalendar()[1],
            'month' : self.now.month,
            'quarter' : self.get_current_quarter(),
            'year' : self.now.year,
        }

class Time:
    def __init__(self):
        self.default_timezone = timezone('Turkey')
        self.now = datetime.now(self.default_timezone)

    def get_current_time(self):
        return {
            'time' : self.now.time(),
            'hour' : self.now.hour,
            'minute' : self.now.minute,
            'second' : self.now.second
        }
    
class CoinData:
    def __init__(self):
        self.headers = {
            'x-access-token': ''
        }

        self.response = requests.request("GET", "https://api.coinranking.com/v2/coins", headers=self.headers)
        self.coin_data = json.loads(self.response.text)

    def clean_coin_data(self):
        coins = self.coin_data['data']['coins']
        NUM_OF_COINS_TO_GET = 5
        coins = coins[0 : NUM_OF_COINS_TO_GET]
        coins_df = pd.DataFrame.from_dict(coins)
        COLUMNS_TO_KEEP = ['uuid', 'symbol', 'name', 'iconUrl', 'price', 'change', 'rank']
        coins_df = coins_df.loc[:, COLUMNS_TO_KEEP]
        coins_df['price'] = coins_df['price'].astype('float').round(2)
        coins_df['change'] = coins_df['change'].astype('float').round(2)
        coins_df.rename(columns={'iconUrl' : 'icon_url'}, inplace=True)
        return coins_df
    
    def get_coin_data(self):
        return self.clean_coin_data()

class CoinPriceData:
    def __init__(self, coins_data: CoinData, date_id, time_id):
        self.coins_df = coins_data.get_coin_data()
        self.date_id = date_id
        self.time_id = time_id
        
    def get_coins_price(self):
        self.coins_df[['date_id', 'time_id']] = self.date_id, self.time_id
        return self.coins_df