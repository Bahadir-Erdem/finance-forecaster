import logging
import azure.functions as func
from src.azure_functions import (
    get_daily_coin_data,
    get_daily_stock_data,
    etl_lightgbm_predict_insert,
)


app = func.FunctionApp()

azure_functions = [
    get_daily_coin_data,
    get_daily_stock_data,
    etl_lightgbm_predict_insert,
]

for function in azure_functions:
    app.register_functions(function.blueprint)
