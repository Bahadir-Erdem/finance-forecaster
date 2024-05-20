from .CoinData import CoinData
from .StockData import StockData
import pandas as pd

class TrainingData:
    def __init__(self):
        self.stock_data = StockData()
        self.coin_data = CoinData()

    def get_training_data(self):
        stock_data = self.stock_data.get_stock_data()
        coin_data = self.coin_data.get_coin_data()
        training_data = pd.concat([coin_data, stock_data], ignore_index=True)
        training_data.dropna(inplace=True)
        return training_data