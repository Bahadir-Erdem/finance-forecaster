import yaml

from src.data_sources.sources import (
    FinancialModellingPrepStockDataInfo,
    UrlWebScraper,
    FinnhubStockPrice,
)
from src.transformations.transformations import DailyStockData
from src.data_targets.targets import DBStockTarget


def run():
    with open("database_config.yaml") as f:
        yaml_dictionary = yaml.safe_load(f)

    top_stocks_config = (
        yaml_dictionary.get("data_sources")
        .get("web_scraping_sources")
        .get("stock_analysis_top_stocks")
    )
    stock_info_config = (
        yaml_dictionary.get("data_sources")
        .get("api_data_sources")
        .get("financial_modeling_prep_stock_info")
    )
    stock_price_config = (
        yaml_dictionary.get("data_sources")
        .get("api_data_sources")
        .get("finnhub_stock_price")
    )
    CONNECTION_STRING = (
        yaml_dictionary.get("data_targets")
        .get("databases")
        .get("remote")
        .get("azure_sql_server")
        .get("connection_string")
    )

    top_stocks_scraper = UrlWebScraper(top_stocks_config["url"])
    stock_data_price_api = FinnhubStockPrice(
        url=stock_price_config["url"], params=stock_price_config["params"]
    )
    stock_data_info_api = FinancialModellingPrepStockDataInfo(
        url=stock_info_config["url"], params=stock_info_config["params"]
    )
    stock_data_transformer = DailyStockData(
        top_stocks_scraper, stock_data_info_api, stock_data_price_api
    )

    stock_save_target = DBStockTarget(CONNECTION_STRING)
    stock_save_target.save(stock_data_transformer)
