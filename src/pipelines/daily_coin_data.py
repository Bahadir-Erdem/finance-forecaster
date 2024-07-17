import yaml

from src.data_sources.sources import APISource
from src.transformations.transformations import CoinrankingToDailyStockData
from src.data_targets.targets import DBCoinTarget


def run():
    with open("database_config.yaml") as f:
        yaml_dictionary = yaml.safe_load(f)

    CONNECTION_STRING = (
        yaml_dictionary.get("data_targets")
        .get("databases")
        .get("remote")
        .get("azure_sql_server")
        .get("connection_string")
    )
    COINRANKING_API_SOURCE = (
        yaml_dictionary.get("data_sources")
        .get("api_data_sources")
        .get("coinranking_daily_coin_data")
    )

    coinranking_api_source = APISource(
        COINRANKING_API_SOURCE["url"], COINRANKING_API_SOURCE["method"]
    )
    coinranking_transformer = CoinrankingToDailyStockData(coinranking_api_source)
    data_target = DBCoinTarget(CONNECTION_STRING)
    data_target.save(coinranking_transformer)
