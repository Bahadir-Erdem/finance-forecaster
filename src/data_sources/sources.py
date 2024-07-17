from abc import ABC, abstractmethod
from datetime import datetime
import logging
from time import sleep
from typing import Optional, Any

import pandas as pd
import requests
from requests.exceptions import RequestException, HTTPError
from bs4 import BeautifulSoup
import yfinance as yf
from dateutil.relativedelta import relativedelta


class DataSource(ABC):
    @abstractmethod
    def get_data(self) -> Any:
        pass


class APISource(DataSource):
    def __init__(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        on_error_wait: int = 30,
        on_error_max_retry: int = 3,
    ):
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.params = params or {}
        self.on_error_wait = on_error_wait
        self.on_error_max_retry = on_error_max_retry
        self._retries = 0

    def get_data(self, url: Optional[str] = None) -> dict:
        url = url or self.url
        while self._retries < self.on_error_max_retry:
            try:
                response = requests.request(
                    method=self.method,
                    url=url,
                    headers=self.headers,
                    params=self.params,
                )
                response.raise_for_status()
                self._retries = 0
                return response.json()
            except HTTPError as e:
                if e.response.status_code == 429:
                    self._handle_rate_limit_exceeded()
                else:
                    logging.error(f"HTTP error fetching data from {url}: {e}")
                    return {}
            except RequestException as e:
                logging.error(f"Error fetching data from {url}: {e}")
                return {}
        return {}

    def _handle_rate_limit_exceeded(self):
        logging.warning(
            f"Rate limit exceeded. Retrying in {self.on_error_wait:.2f} seconds..."
        )
        sleep(self.on_error_wait)
        self._retries += 1


class UrlWebScraper(DataSource):
    def __init__(self, url: str):
        self.url = url

    def get_data(self) -> pd.DataFrame:
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table")

        if not table:
            return pd.DataFrame()

        headers = [th.text.strip() for th in table.find_all("th")]
        data = [
            [td.text.strip() for td in row.find_all("td")]
            for row in table.find_all("tr")
        ]

        return pd.DataFrame(data, columns=headers).dropna(how="all")


class FinancialModellingPrepStockDataInfo(APISource):
    def get_data(self, symbol: str) -> dict:
        url = self.url.replace("<symbol>", symbol)
        data = super().get_data(url)
        return data[0] if data else {}


class FinnhubStockPrice(APISource):
    def get_data(self, symbol: str) -> dict:
        url = self.url.replace("<symbol>", symbol)
        return super().get_data(url)


class YahooStockPriceHistory(DataSource):
    def get_data(self, symbols: list, past_num_of_years: int) -> pd.DataFrame:
        end_date = datetime.now()
        start_date = end_date - relativedelta(years=past_num_of_years)

        data = []
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            history = ticker.history(start=start_date, end=end_date)
            if not history.empty:
                history["symbol"] = symbol
                data.append(history)

        return pd.concat(data) if data else pd.DataFrame()


class CoinrankingCoinPriceHistory(APISource):
    def get_data(self, uuid: str) -> dict:
        url = self.url.replace("<uuid>", uuid)
        self.data = super().get_data(url)
        return self.data
