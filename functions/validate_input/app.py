import logging
from dataclasses import dataclass
from enum import Enum
from os import environ
from typing import Optional
from uuid import UUID

from aws_xray_sdk.core import patch_all, xray_recorder

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

xray_recorder.configure(service="StaxOrchestrator:ValidateInput")
patch_all()


class WorkloadOperation(Enum):
    DEPLOY = "deploy"
    UPDATE = "update"


@dataclass(frozen=True, order=True)
class WorkloadEvent:
    aws_account_id: int
    aws_region: str
    catalogue_id: UUID
    workload_name: str
    workload_parameters: Optional[dict] = None
    workload_tags: Optional[dict] = None


class MissingRequiredInput(Exception):
    """Raised when required user inputs are not present"""


def lambda_handler(event, _) -> WorkloadEvent.__dict__:
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
        raise MissingRequiredInput(f"Missing required input key: {missing_key}")

    if "workload_parameters" in event:
        workload_kwargs["workload_parameters"] = event["workload_parameters"]

    if "workload_tags" in event:
        workload_kwargs["workload_tags"] = event["workload_tags"]

    if event["operation"] == "deploy":
        event["workload_create_payload"] = WorkloadEvent(**workload_kwargs).__dict__
    else:
        event["workload_update_payload"] = WorkloadEvent(**workload_kwargs).__dict__

    return event
