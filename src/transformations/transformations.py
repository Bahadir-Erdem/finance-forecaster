from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
from pytz import timezone
import pandas as pd

from src.ml.model import Model
from src.data_sources.sources import (
    APISource,
    CoinrankingCoinPriceHistory,
    FinancialModellingPrepStockDataInfo,
    FinnhubStockPrice,
    UrlWebScraper,
    YahooStockPriceHistory,
)


class Transformer(ABC):
    def __init__(self) -> None:
        self.processed_data = None

    @abstractmethod
    def transform(self) -> pd.DataFrame:
        pass


class Date:
    def __init__(self):
        self.default_timezone = timezone("Turkey")
        self.now = datetime.now(self.default_timezone)

    def get_current_quarter(self, datetime_value: datetime) -> int:
        current_date = datetime_value or self.now
        quarter = (current_date.month - 1) // 3 + 1
        return quarter

    def _create_date_dict(self, now: datetime) -> dict:
        return {
            "date": now.date(),
            "day": now.day,
            "week": now.isocalendar()[1],
            "month": now.month,
            "quarter": self.get_current_quarter(now),
            "year": now.year,
        }

    def get_current_date(
        self, datetime_value: Optional[datetime | pd.Series] = None
    ) -> pd.DataFrame:
        if isinstance(datetime_value, pd.Series):
            date_dict_list = []
            for value in datetime_value:
                now = value if datetime_value.notnull().any() else self.now
                date_dict_list.append(self._create_date_dict(now))
            return pd.DataFrame(date_dict_list)

        now = datetime_value or self.now
        return pd.DataFrame([self._create_date_dict(now)], index=[0])

    def merge_with_date(self, data: pd.DataFrame) -> pd.DataFrame:
        if "datetime" not in data.columns:
            data["datetime"] = pd.to_datetime(pd.NaT)

        datetime = data["datetime"]
        date = self.get_current_date(datetime)
        df_with_time = pd.concat([data, date], axis=1)
        return df_with_time


class Time:
    def __init__(self):
        self.default_timezone = timezone("Turkey")
        self.now = datetime.now(self.default_timezone)

    def _create_time_dict(self, now: datetime) -> dict:
        return {
            "time": now.time(),
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
        }

    def get_current_time(
        self, datetime_value: Optional[datetime | pd.Series] = None
    ) -> pd.DataFrame:
        if isinstance(datetime_value, pd.Series):
            time_dict_list = []
            for value in datetime_value:
                now = value if datetime_value.notnull().any() else self.now
                time_dict_list.append(self._create_time_dict(now))
            return pd.DataFrame(time_dict_list)

        now = datetime_value or self.now
        return pd.DataFrame([self._create_time_dict(now)])

    def merge_with_time(self, data: pd.DataFrame) -> pd.DataFrame:
        if "datetime" not in data.columns:
            data["datetime"] = pd.to_datetime(pd.NaT)

        datetime = data["datetime"]
        time = self.get_current_time(datetime)
        df_with_time = pd.concat([data, time], axis=1)
        return df_with_time


class CoinrankingToDailyStockData(Transformer):
    COLUMNS_TO_KEEP = [
        "uuid",
        "symbol",
        "name",
        "iconUrl",
        "price",
        "change",
        "rank",
    ]

    def __init__(self, api_source: APISource, num_of_coins_to_hold: int = 5):
        super().__init__()
        self.api_source = api_source
        self.raw_data = api_source.get_data()
        self.processed_data = None
        self.NUM_OF_COINS_TO_HOLD = num_of_coins_to_hold
        self.date = Date()
        self.time = Time()

    def clean_coin_data(self):
        coins = self.raw_data["data"]["coins"]
        coins = coins[0 : self.NUM_OF_COINS_TO_HOLD]
        coins_df = pd.DataFrame.from_dict(coins)
        coins_df = coins_df.loc[:, self.COLUMNS_TO_KEEP]
        coins_df["price"] = coins_df["price"].astype("float").round(2)
        coins_df["change"] = coins_df["change"].astype("float").round(2)
        coins_df.rename(columns={"iconUrl": "icon_url"}, inplace=True)
        return coins_df

    def transform(self) -> pd.DataFrame:
        data = self.clean_coin_data()
        df_with_time = self.time.merge_with_time(data)
        self.processed_data = self.date.merge_with_date(df_with_time)
        return self.processed_data

    def get_processed_data():
        pass


class DailyStockData(Transformer):
    def __init__(
        self,
        url_web_scraper: UrlWebScraper,
        stock_data_info: FinancialModellingPrepStockDataInfo,
        stock_price: FinnhubStockPrice,
        num_of_stock_to_get: int = 5,
    ) -> None:
        super().__init__()
        self.url_web_scraper = url_web_scraper
        self.stock_data_info = stock_data_info
        self.stock_price = stock_price
        self.NUM_OF_STOCK_TO_GET = num_of_stock_to_get
        self.time = Time()
        self.date = Date()

    def transform(self) -> pd.DataFrame:
        self.stock_symbols = self.clean_top_stocks()
        stocks_df_all = self.get_stock_data(self.stock_symbols)
        stocks_df = self.clean_stock_data(stocks_df_all)
        stocks_df = self.time.merge_with_time(stocks_df)
        self.processed_data = self.date.merge_with_date(stocks_df)
        return self.processed_data

    def clean_top_stocks(self) -> list:
        top_stocks = self.url_web_scraper.get_data()

        top_stocks.drop(columns="No.", inplace=True)
        top_stocks["% Change"] = pd.to_numeric(
            top_stocks["% Change"].str.rstrip("%"), errors="coerce"
        ).fillna(0)

        top_stocks = top_stocks.map(
            lambda x: x.replace(",", "") if isinstance(x, str) else x
        )

        for col in ["Market Cap", "Revenue"]:
            top_stocks[col] = top_stocks[col].str.rstrip("B")

        top_stocks["Revenue"] = top_stocks["Revenue"].replace("-", "0")
        top_stocks.loc[top_stocks["Revenue"].str.endswith("M"), "Revenue"] = "39.48"

        float_columns = ["Market Cap", "Stock Price", "Revenue"]
        top_stocks[float_columns] = top_stocks[float_columns].astype(float)

        top_stocks = top_stocks.sort_values(by="Market Cap", ascending=False)
        stock_symbols = top_stocks["Symbol"].head(self.NUM_OF_STOCK_TO_GET)

        return stock_symbols

    def get_stock_data(self, symbols):
        data = []
        for symbol in symbols:
            stock_info_dict = self.stock_data_info.get_data(symbol)
            stock_price_dict = self.stock_price.get_data(symbol)

            if stock_info_dict and stock_price_dict:
                data.append({**stock_info_dict, **stock_price_dict})

        return pd.DataFrame.from_dict(data)

    def clean_stock_data(self, df: pd.DataFrame):
        COLUMN_MAPPING = {
            "symbol": "symbol",
            "companyName": "company_name",
            "exchangeShortName": "exchange",
            "image": "icon_url",
            "industry": "industry",
            "t": "datetime",
            "c": "close",
            "h": "high",
            "l": "low",
            "o": "open",
        }
        df = df.loc[:, COLUMN_MAPPING.keys()].rename(columns=COLUMN_MAPPING)
        df["datetime"] = df["datetime"].apply(lambda x: datetime.fromtimestamp(x))
        return df


class StockTrainingData(Transformer):
    def __init__(
        self,
        url_web_scraper: UrlWebScraper,
        stock_history_source: YahooStockPriceHistory,
        past_num_of_years: int = 1,
        num_of_stock: int = 5,
    ) -> None:
        super().__init__()
        self.url_web_scraper = url_web_scraper
        self.stock_history_source = stock_history_source
        self.past_num_of_years = past_num_of_years
        self.num_of_stock = num_of_stock

    def transform(self) -> pd.DataFrame:
        top_stocks = self.url_web_scraper.get_data().loc[:, "Symbol"]
        top_stocks = top_stocks[0 : self.num_of_stock]
        raw_stock_data = self.stock_history_source.get_data(
            top_stocks, self.past_num_of_years
        )
        self.processed_data = self.clean_stock_data(raw_stock_data)
        return self.processed_data

    def clean_stock_data(self, stock_dataset: pd.DataFrame) -> pd.DataFrame:
        COLUMN_MAPPING = {"Close": "price", "symbol": "entity", "Date": "datetime"}
        stock_dataset = stock_dataset.tz_localize(None)
        stock_dataset = stock_dataset.reset_index()
        stock_dataset = stock_dataset.loc[:, COLUMN_MAPPING.keys()]
        stock_dataset.rename(columns=COLUMN_MAPPING, inplace=True)
        stock_dataset["year"] = stock_dataset["datetime"].dt.year
        stock_dataset["month"] = stock_dataset["datetime"].dt.month
        stock_dataset["day"] = stock_dataset["datetime"].dt.day
        return stock_dataset


class CoinTrainingData(Transformer):
    def __init__(
        self,
        coin_uuid_source: APISource,
        coin_price_source: CoinrankingCoinPriceHistory,
        past_num_of_years: int = 1,
        num_of_coin: int = 5,
    ) -> None:
        super().__init__()
        self.coin_uuid_source = coin_uuid_source
        self.coin_price_source = coin_price_source
        self.past_num_of_years = past_num_of_years
        self.num_of_coin = num_of_coin

    def transform(self) -> pd.DataFrame:
        raw_uuids = self.coin_uuid_source.get_data()
        uuids = self.clean_uuids(raw_uuids)
        self.processed_data = self.get_coin_price_history(uuids)
        return self.processed_data

    def clean_uuids(self, uuids_dict: dict) -> list:
        coin_data = uuids_dict["data"]["coins"]
        coin_uuids = [coin["uuid"] for coin in coin_data]
        return coin_uuids

    def get_coin_price_history(self, uuids: list):
        coin_dataset = []

        for uuid in uuids:
            data = self.coin_price_source.get_data(uuid)
            coin_df = self.clean_coin_data(data, uuid)
            coin_dataset.append(coin_df)

        coin_dataset = pd.concat(coin_dataset)
        coin_dataset["datetime"] = pd.to_datetime(
            coin_dataset[["year", "month", "day"]]
        )
        return coin_dataset

    def clean_coin_data(self, data: dict, uuid: str) -> pd.DataFrame:
        df = pd.DataFrame.from_dict(data["data"]["history"])
        df["timestamp"] = df["timestamp"].apply(lambda x: datetime.fromtimestamp(x))
        column_renaming_dict = {"timestamp": "datetime"}
        df.rename(columns=column_renaming_dict, inplace=True)
        df["price"] = df["price"].astype(float)
        df["entity"] = uuid
        df["year"] = df["datetime"].dt.year
        df["month"] = df["datetime"].dt.month
        df["day"] = df["datetime"].dt.day
        return df


class ModelTrainingData(Transformer):
    def __init__(
        self, stock_transformer: StockTrainingData, coin_transformer: CoinTrainingData
    ) -> None:
        super().__init__()
        self.stock_transformer = stock_transformer
        self.coin_transformer = coin_transformer

    def transform(self) -> pd.DataFrame:
        coin_dataset = self.coin_transformer.transform()
        stock_dataset = self.stock_transformer.transform()
        self.processed_data = pd.concat(
            [coin_dataset, stock_dataset], ignore_index=True
        )
        self.processed_data.dropna(inplace=True)
        return self.processed_data


class PredictionsData(Transformer):
    def __init__(
        self, training_data_transformer: ModelTrainingData, model: Model
    ) -> None:
        super().__init__()
        self.trainig_data_transformer = training_data_transformer
        self.model = model

    def transform(self) -> pd.DataFrame:
        self.results = []

        training_df = self.trainig_data_transformer.transform()

        for entity in training_df["entity"].unique():
            train_dataset = training_df.loc[
                training_df["entity"] == entity, training_df.columns != "entity"
            ]
            predictions, result = self.model.lightgbm(train_dataset)
            self.clean_predictions(entity, predictions, result)
            self.results.append(result)

        self.processed_data = pd.concat(self.results)
        return self.processed_data

    def clean_predictions(self, entity, predictions, result):
        result["predicted_values"] = predictions
        result["entity"] = entity
        result["datetime"] = pd.to_datetime(result[["year", "month", "day"]])
        result.drop(columns=["year", "month", "day"], inplace=True)
        return result
