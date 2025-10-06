from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret
from tiled.client import from_profile
import os
import pytest
from utils import get_tiled_client

tiled_client_chx = get_tiled_client()["raw"]
tiled_client_sandbox = get_tiled_client()["sandbox"]
tiled_client_processed = get_tiled_client()["processed"]


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
    run = tiled_client_chx[ref]
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
