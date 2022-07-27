import logging
from os import environ

from aws_xray_sdk.core import patch_all, xray_recorder

from stax_orchestrator import StaxOrchestrator

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

xray_recorder.configure(service="StaxOrchestrator:CreateWorkload")
patch_all()


def lambda_handler(event, _) -> dict:
    """Create Stax Workloads Lambda Handler"""
    stax_orchestrator = StaxOrchestrator()
    event["create_workload_response"] = stax_orchestrator.create_workload(
        **event["workload_create_payload"]
    )

    return event
