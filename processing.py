from prefect import flow, task, get_run_logger
from data_validation import get_run
from dotenv import load_dotenv
import os
import pytest


def get_api_key_from_env(api_key=None):
    with open("/srv/container.secret", "r") as secrets:
        load_dotenv(stream=secrets)
    api_key = os.environ["TILED_API_KEY"]
    return api_key


@task(retries=2, retry_delay_seconds=10)
def get_run(uid, api_key=None):
    if not api_key:
        api_key = get_api_key_from_env()
    cl = from_uri("https://tiled.nsls2.bnl.gov", api_key=api_key)
    run = cl["chx/raw"][uid]
    return run


@task
def process_run(ref):
    """
    Do processing on a BlueSky run.

    Parameters
    ----------
    ref : int, str
        reference to BlueSky. It can be scan_id, uid or index
    """

    logger = get_run_logger()
    # Grab the BlueSky run
    run = get_run(ref)
    # Grab the full uid for logging purposes
    full_uid = run.start["uid"]
    logger.info(f"{full_uid = }")
    logger.info("Do something with this uid")
    logger.info("Now do something else with this uid")
    # Do some additional processing or call otehr python processing functions


@flow
def processing_flow(ref):
    """
    Prefect flow to do processing on a BlueSky run.

    Parameters
    ----------
    ref : int, str
        reference to BlueSky. It can be scan_id, uid or index
    """

    process_run(ref)
