from prefect import task, flow, get_run_logger
from data_validation import data_validation
from processing import processing_flow


@task
def log_completion():
    logger = get_run_logger()
    logger.info("Complete")


@flow
def end_of_run_workflow(stop_doc, api_key=None):
    uid = stop_doc["run_start"]
    # return_state = True delays raising exceptions until the end of the validation
    # data_validation(uid, api_key=api_key)
    processing_flow(uid, api_key=api_key)
    log_completion()
