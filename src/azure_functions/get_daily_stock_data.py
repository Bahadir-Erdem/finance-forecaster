import logging
import azure.functions as func
from src.pipelines import daily_stock_data

logger = logging.getLogger(__name__)

blueprint = func.Blueprint()


@blueprint.timer_trigger(
    schedule="0 15 12 * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def timer_trigger_get_daily_stock_data(myTimer: func.TimerRequest) -> None:
    """
    Azure Function timer trigger to get daily stock data.
    Runs daily at 12:15 PM UTC time.
    """
    logger.info("Timer trigger function started.")

    if myTimer.past_due:
        logger.warning("The timer is past due!")

    try:
        daily_stock_data.run()
        logger.info("Daily stock data retrieved successfully.")
    except Exception as e:
        logger.error(
            f"An error occurred while getting daily stock data: {str(e)}", exc_info=True
        )
        raise e

    logger.info("Timer trigger function completed.")
