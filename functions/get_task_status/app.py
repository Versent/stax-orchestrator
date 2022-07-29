import logging
from os import environ

from aws_xray_sdk.core import patch_all, xray_recorder

from stax_orchestrator import StaxOrchestrator

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

xray_recorder.configure(service="StaxOrchestrator:GetTaskStatus")
patch_all()


def lambda_handler(event, _) -> dict:
    stax_orchestrator = StaxOrchestrator()
    logging.info(f"EVENT: {event}")
    event["task_info"] = "NOTFOUND"
    try:
        event["task_info"] = stax_orchestrator.get_task_status(event["task_id"])
    except:
        logging.warning(f"Task with ID {event['task_id']} not found!")
    logging.info(f"task_status: {event['task_info']['Status']}")
    return event
