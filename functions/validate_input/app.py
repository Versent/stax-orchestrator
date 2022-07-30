"""
    Validate input to the workload state machine
"""
import logging
from os import environ

from aws_xray_sdk.core import patch_all, xray_recorder

from stax_orchestrator import MissingRequiredInput, WorkloadEvent

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

xray_recorder.configure(service="StaxOrchestrator:ValidateInput")
patch_all()


def lambda_handler(event: dict, _) -> WorkloadEvent.__dict__:
    """Validate input to workload state machine

    Args:
        event (dict): Details about the workload to be deployed or updated

    Returns:
        WorkloadEvent: Details about the catalogue, workload and account

    Raises:
        KeyError: Raised when required event arguments are not present
    """
    workload_kwargs = {}

    try:
        workload_kwargs = {
            "aws_account_id": event["aws_account_id"],
            "aws_region": event["aws_region"],
            "catalogue_id": event["catalogue_id"],
            "workload_name": event["workload_name"],
        }

    except KeyError as missing_key:
        raise MissingRequiredInput(
            f"Missing required input key: {missing_key} from the event payload."
        ) from missing_key

    if "workload_parameters" in event:
        workload_kwargs["workload_parameters"] = event["workload_parameters"]

    if "workload_tags" in event:
        workload_kwargs["workload_tags"] = event["workload_tags"]

    return WorkloadEvent(**workload_kwargs).__dict__
