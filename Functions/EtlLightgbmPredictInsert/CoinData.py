import requests
from datetime import datetime
import pandas as pd

class CoinData:
    def __init__(self):
        self.api_key = ''

    def get_coin_uuids(self):
        SCOPE_ID = 'marketCap'
        SCOPE_LIMIT = 10
        url = f"https://api.coinranking.com/v2/coins?scopeId={SCOPE_ID}&scopeLimit={SCOPE_LIMIT}"
        headers = {"x-access-token": self.api_key}
        response = requests.get(url, headers=headers)
        data = response.json()
        coin_data = data['data']['coins']
        coin_uuids = [coin['uuid'] for coin in coin_data]
        return coin_uuids

    def clean_coin_data(self, data: dict, uuid):
        df = pd.DataFrame.from_dict(data['data']['history'])
        df['timestamp'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(x))
        column_renaming_dict = {'timestamp': 'datetime'}
        df.rename(columns=column_renaming_dict, inplace=True)
        df['price'] = df['price'].astype(float)
        df['entity'] = uuid
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        df['day'] = df['datetime'].dt.day
        df.drop(columns='datetime', inplace=True)
        return df

    def get_coin_price_history(self, uuids: list):
        time_period = '5y'
        headers = {"x-access-token": self.api_key}
        coin_dataset = []

        for uuid in uuids:
            url = f"https://api.coinranking.com/v2/coin/{uuid}/history?timePeriod={time_period}"
            response = requests.get(url, headers=headers)
            data = response.json()
            coin_df = self.clean_coin_data(data, uuid)
            coin_dataset.append(coin_df)
        return pd.concat(coin_dataset)

    def get_coin_data(self):
        uuids = self.get_coin_uuids()
        coin_df = self.get_coin_price_history(uuids)
        return coin_df