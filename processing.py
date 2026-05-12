from prefect import flow, task, get_run_logger
from data_validation import get_run
import pytest


@task
def process_run(ref, api_key=None):
    """
    Do processing on a BlueSky run.

    Parameters
    ----------
    ref : int, str
        reference to BlueSky. It can be scan_id, uid or index
    """

    logger = get_run_logger()
    # Grab the BlueSky run
    run = get_run(ref, api_key=api_key)
    # Grab the full uid for logging purposes
    full_uid = run.start["uid"]
    logger.info(f"{full_uid = }")
    logger.info("Do something with this uid")
    logger.info("Now do something else with this uid")
    # Do some additional processing or call otehr python processing functions


@flow
def processing_flow(ref, api_key=None):
    """
    Prefect flow to do processing on a BlueSky run.

    Parameters
    ----------
    ref : int, str
        reference to BlueSky. It can be scan_id, uid or index
    """

    process_run(ref, api_key=api_key)
