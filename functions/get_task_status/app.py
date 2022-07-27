import logging
from os import environ

from aws_xray_sdk.core import patch_all, xray_recorder

from stax_orchestrator import StaxOrchestrator

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

xray_recorder.configure(service="StaxOrchestrator:GetTaskStatus")
patch_all()


def lambda_handler(event, _) -> dict:
    stax_orchestrator = StaxOrchestrator()
    task_status = stax_orchestrator.get_task_status(
        event["create_workload_response"]["task_id"]
    )

    logging.debug(f"task_status: {task_status}")
    event["task_status"] = task_status

    return event
