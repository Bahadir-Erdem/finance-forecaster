# Register this blueprint by adding the following line of code 
# to your entry point file.  
# app.register_functions(blueprint) 
# 
# Please refer to https://aka.ms/azure-functions-python-blueprints

import logging
import azure.functions as func
from .Database import Database
from .Entity import CoinData, CoinPriceData, Date, Time



timer_trigger_get_daily_coin_data_blueprint = func.Blueprint()


@timer_trigger_get_daily_coin_data_blueprint.timer_trigger(schedule="0 0 12 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger_get_daily_coin_data(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    
    server = ''
    database = ''
    username = ''
    password = '' 
    driver = ''

    database = Database(server, database, username, password, driver)
    conn = database.connect()
    
    if conn is not None:
        date = Date()
        date_id = database.insert_date(date)
        time = Time()
        time_id = database.insert_time(time)
        coin_data = CoinData()
        database.insert_or_update_coin_data(coin_data)
        coin_price_data = CoinPriceData(coin_data, date_id, time_id)
        database.insert_or_update_coin_data_ft(coin_price_data)
        database.close()
        logging.info('Code executed with success')
    else:
        logging.fatal("Error connecting to the database.")

    logging.info('Python timer trigger function executed.')