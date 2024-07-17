import logging
import azure.functions as func
from src.pipelines import ml_price_prediction

logger = logging.getLogger(__name__)

blueprint = func.Blueprint()


@blueprint.timer_trigger(
    schedule="0 0 6 * * 1", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def etl_lightgbm_predict_insert(myTimer: func.TimerRequest) -> None:
    """
    Azure Function timer trigger to get predictions of coin and stock data using Lightgbm.
    Runs every monday at 06:00 AM UTC time.
    """
    logger.info("Timer trigger function started.")

    if myTimer.past_due:
        logging.info("The timer is past due!")

    try:
        ml_price_prediction.run()
        logger.info("Daily coin data retrieved successfully.")
    except Exception as e:
        logger.error(
            f"An error occurred while getting daily coin data: {str(e)}", exc_info=True
        )
        raise e

    logger.info("Timer trigger function completed.")
