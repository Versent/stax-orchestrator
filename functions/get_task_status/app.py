"""
    Get status of a Stax workload task.
"""
import logging
from os import environ

from aws_xray_sdk.core import patch_all, xray_recorder

from stax_orchestrator import StaxOrchestrator

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

xray_recorder.configure(service="StaxOrchestrator:GetTaskStatus")
patch_all()


def lambda_handler(event: dict, _) -> dict:
    """
    Poll for a Stax workload task status

    Args:
        event (dict): Event data containing workload and task ID

    Returns:
        dict: Event including task status
    """
    logging.debug(f"event: {event}")
    event["task_info"] = StaxOrchestrator().get_task_status(event["task_id"])

    return event
