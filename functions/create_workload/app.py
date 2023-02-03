"""
    Deploy a Stax workload and return response data containing workload and task information
"""
import logging
from os import environ

from aws_xray_sdk.core import patch_all, xray_recorder

from src.stax_orchestrator import StaxOrchestrator

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

xray_recorder.configure(service="StaxOrchestrator:CreateWorkload")
patch_all()


def lambda_handler(event: dict, _) -> dict:
    """Create Stax Workloads Lambda Handler"""
    stax_orchestrator = StaxOrchestrator()

    if stax_orchestrator.workload_with_name_already_exists(event["workload_name"]):
        raise stax_orchestrator.WorkloadWithNameAlreadyExistsException(
            f"Workload with name {event['workload_name']} already exists"
        )

    return stax_orchestrator.create_workload(**event)
