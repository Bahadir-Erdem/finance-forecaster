# Register this blueprint by adding the following line of code 
# to your entry point file.  
# app.register_functions(__init__) 
# 
# Please refer to https://aka.ms/azure-functions-python-blueprints

import logging
import azure.functions as func
from .Database import Database
from .PredictionsData import PredictionsData

etl_lightgbm_predict_insert_blueprint = func.Blueprint()


@etl_lightgbm_predict_insert_blueprint.timer_trigger(schedule="0 0 11 * * 1", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def etl_lightgbm_predict_insert(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    
    server = ''
    database = ''
    username = ''
    password = '' 
    driver = ''
    database = Database(driver, server, database, username, password)

    with database.connect() as db:
        predictins_data = PredictionsData(db)
        predictins_data.predict_and_to_db()
        logging.info('Code executed with success!')


    logging.info('Python timer trigger function executed.')