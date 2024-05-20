import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import yfinance as yf

class StockData:
    def __init__(self, past_num_of_years=5):
        self.past_num_of_years = past_num_of_years

    def scrape_top_stocks(self):
        url = "https://stockanalysis.com/list/biggest-companies/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table")
        headers = [th.text.strip() for th in table.find_all("th")]
        data = []
        for row in table.find_all("tr"):
            row_data = [td.text.strip() for td in row.find_all("td")]
            if row_data:
                data.append(row_data)
        return pd.DataFrame(data, columns=headers)

    def clean_top_stocks(self, top_stocks: pd.DataFrame):
        top_stocks.drop(columns='No.', inplace=True)
        top_stocks['% Change'] = pd.to_numeric(top_stocks['% Change'].str.replace('%', ''), errors='coerce').fillna(0)
        top_stocks = top_stocks.map(lambda x: x.replace(',', '') if type(x) == str else x)
        top_stocks['Market Cap'].loc[~top_stocks['Market Cap'].str.endswith('B')]
        top_stocks['Revenue'].loc[~top_stocks['Market Cap'].str.endswith('B')]
        top_stocks[['Market Cap', 'Revenue']] = top_stocks[['Market Cap', 'Revenue']].map(lambda x: x.rstrip('B') if type(x) is str else x)
        top_stocks['Revenue'] = top_stocks['Revenue'].str.replace('-', '0')
        top_stocks.loc[top_stocks['Revenue'].str.endswith('M'), 'Revenue'] = '39.48'
        top_stocks.loc[:, ['Market Cap', 'Stock Price', 'Revenue']] = top_stocks[['Market Cap', 'Stock Price', 'Revenue']].astype('float')
        top_stocks = top_stocks.sort_values(by='Market Cap', ascending=False)
        stock_symbols = top_stocks.loc[0:10, 'Symbol']
        return stock_symbols

    def get_stock_price_history(self, symbols):
        today = datetime.now()
        past = today - relativedelta(years=self.past_num_of_years)

        dataset = []
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=past, end=today)
            if not data.empty:
                data['symbol'] = symbol
                dataset.append(data)
        return pd.concat(dataset)

    def clean_stock_data(self, stock_dataset: pd.DataFrame):
        stock_dataset = stock_dataset.reset_index()
        STOCK_COLUMNS_TO_KEEP = ['Date', 'Close', 'symbol']
        stock_dataset = stock_dataset.loc[:, STOCK_COLUMNS_TO_KEEP]
        stock_dataset['year'] = stock_dataset['Date'].dt.year
        stock_dataset['month'] = stock_dataset['Date'].dt.month
        stock_dataset['day'] = stock_dataset['Date'].dt.day
        stock_dataset.drop(columns='Date', inplace=True)
        stock_dataset.rename(columns={'Close': 'price', 'symbol': 'entity'}, inplace=True)
        return stock_dataset

    def get_stock_data(self):
        top_stocks = self.scrape_top_stocks()
        top_stocks_symbols = self.clean_top_stocks(top_stocks)
        stock_dataset = self.get_stock_price_history(top_stocks_symbols)
        stock_dataset = self.clean_stock_data(stock_dataset)
        return stock_dataset