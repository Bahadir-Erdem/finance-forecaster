import yaml

from src.data_targets.targets import DBPredictionTarget
from src.ml.model import Model
from src.data_sources.sources import (
    APISource,
    CoinrankingCoinPriceHistory,
    UrlWebScraper,
    YahooStockPriceHistory,
)
from src.transformations.transformations import (
    CoinTrainingData,
    ModelTrainingData,
    PredictionsData,
    StockTrainingData,
)


def run():
    with open("database_config.yaml") as f:
        yaml_dictionary = yaml.safe_load(f)

    top_stocks_config = (
        yaml_dictionary.get("data_sources")
        .get("web_scraping_sources")
        .get("stock_analysis_top_stocks")
    )
    uuid_source_config = (
        yaml_dictionary.get("data_sources")
        .get("api_data_sources")
        .get("coinranking_coin_uuid")
    )
    stock_price_config = (
        yaml_dictionary.get("data_sources")
        .get("api_data_sources")
        .get("coinranking_coin_price_history")
    )
    uuid_source = APISource(
        uuid_source_config["url"],
        uuid_source_config["method"],
        uuid_source_config["headers"],
        uuid_source_config["params"],
    )
    coin_price_history = CoinrankingCoinPriceHistory(
        stock_price_config["url"],
        stock_price_config["method"],
        stock_price_config["headers"],
        stock_price_config["params"],
    )
    PIPELINE = yaml_dictionary.get("pipelines").get("ml_price_prediction")
    CONNECTION_STRING = (
        yaml_dictionary.get("data_targets")
        .get("databases")
        .get("remote")
        .get("azure_sql_server")
        .get("connection_string")
    )
    MAX_RETRY_COUNT_ON_FAIL = (
        yaml_dictionary.get("pipelines").get("general").get("max_retry_count_on_fail")
    )

    top_stocks_scraper = UrlWebScraper(top_stocks_config["url"])
    stock_price_history = YahooStockPriceHistory()

    stock_transformer = StockTrainingData(
        top_stocks_scraper,
        stock_price_history,
        PIPELINE["past_number_of_years_stock_price_history"],
        PIPELINE["number_of_stock_to_get"],
    )
    coin_transformer = CoinTrainingData(
        uuid_source,
        coin_price_history,
        PIPELINE["past_number_of_years_coin_price_history"],
        PIPELINE["number_of_coin_to_get"],
    )
    training_data_transformer = ModelTrainingData(stock_transformer, coin_transformer)

    model = Model(PIPELINE["number_of_days_to_predict"])
    prediction_transformer = PredictionsData(training_data_transformer, model)

    target = DBPredictionTarget(CONNECTION_STRING, max_retries=MAX_RETRY_COUNT_ON_FAIL)
    target.save(prediction_transformer)
