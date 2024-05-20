import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class StockDataFetcher:
    def __init__(self) -> None:
        pass

    def fetch(self):
        top_stocks_df = self.scrape_top_stocks()
        top_stocks = self.clean_top_stocks(top_stocks_df)
        stocks_df_all = self.get_stock_data(top_stocks)
        self.stocks_df = self.clean_stock_data(stocks_df_all)
        return self.stocks_df.copy()

    def scrape_top_stocks(self):
        # Send a GET request to the website
        url = "https://stockanalysis.com/list/biggest-companies/"
        response = requests.get(url)

        # Create a BeautifulSoup object
        soup = BeautifulSoup(response.text, "lxml")

        # Find the table element
        table = soup.find("table")

        # Extract the table headers
        headers = [th.text.strip() for th in table.find_all("th")]

        # Extract the table data
        data = []
        for row in table.find_all("tr"):
            row_data = [td.text.strip() for td in row.find_all("td")]
            if row_data:
                data.append(row_data)
        
        return pd.DataFrame(data, columns=headers)
    
    def clean_top_stocks(self, top_stocks: pd.DataFrame):
        NUM_OF_STOCK_TO_GET = 5
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
        stock_symbols = top_stocks.loc[0 : NUM_OF_STOCK_TO_GET, 'Symbol']
        return stock_symbols
    
    def get_newest_stock_prices(self, symbol) -> dict:
        API_KEY = 'cmah5v1r01qid8geg3egcmah5v1r01qid8geg3f0'
        """
        Retrieves the newest stock prices for a list of symbols using the Finnhub API.

        Args:
            symbols (list): A list of stock symbols.
            api_key (str): The Finnhub API key.

        Returns:
            list: A list of dictionaries containing the newest stock price data for each symbol.
        """

        url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": symbol,
            "token": API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data.get("c") is not None:
            return data
        else:
            raise ValueError(f"Error retrieving data: {data.get('error')}")
        
    def get_stock_info(self, symbol) -> dict:
        """
        Retrieves the newest stock prices for a list of symbols using the Financial Modeling Prep API.

        Args:
            symbols (list): A list of stock symbols.
            api_key (str): The Financial Modeling Prep API key.

        Returns:
            list: A list of dictionaries containing the newest stock price data for each symbol.
        """
        API_KEY = 'oCWHOmLf720nGdABX6rlgyFU3O7anlLc'
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={API_KEY}"

        try:
            response = requests.get(url)
            data = response.json()[0]
        except IndexError:
            return None
        
        return data

    def get_stock_data(self, symbols):
        data = []
        for symbol in symbols:
            stock_info_dict = self.get_stock_info(symbol)
            stock_price_dict = self.get_newest_stock_prices(symbol)

            if any(dict_var is None for dict_var in (stock_info_dict, stock_price_dict)):
                pass
            else:
                stock_dict = {**stock_info_dict, **stock_price_dict}
                data.append(stock_dict)
            
        return pd.DataFrame.from_dict(data)
    
    def clean_stock_data(self, df: pd.DataFrame):
        COLUMNS_TO_KEEP = ['symbol', 'companyName',
                            'exchangeShortName','image',
                            'industry', 't', 'c', 'h',
                            'l', 'o']
        NEW_COLUMN_NAMES = {
            'companyName' : 'company_name',
            'exchangeShortName': 'exchange',
            'image' : 'icon_url',
            't': 'datetime',
            'c': 'close',
            'h': 'high',
            'l': 'low',
            'o': 'open'
        }

        df = df.loc[:, COLUMNS_TO_KEEP]
        df.rename(columns=NEW_COLUMN_NAMES, inplace=True)
        df['datetime'] = df['datetime'].apply(lambda x: datetime.fromtimestamp(x))
        df[['date_id', 'time_id']] = None
        
        return df