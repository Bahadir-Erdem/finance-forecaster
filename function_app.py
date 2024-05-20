import logging
import azure.functions as func
from Functions.TimerTriggerGetDailyCoinData import timer_trigger_get_daily_coin_data_blueprint
from Functions.TimerTriggerGetDailyStockData import timer_trigger_get_daily_stock_data_blueprint
from Functions.EtlLightgbmPredictInsert import etl_lightgbm_predict_insert_blueprint


app = func.FunctionApp()


blueprints = [
    timer_trigger_get_daily_coin_data_blueprint,
    timer_trigger_get_daily_stock_data_blueprint,
    etl_lightgbm_predict_insert_blueprint
]

for blueprint in blueprints:
    app.register_functions(blueprint)


