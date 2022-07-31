"""
    Delete a Stax workload and return response data containing workload and task information
"""
import logging
from os import environ

from aws_xray_sdk.core import patch_all, xray_recorder

from stax_orchestrator import StaxOrchestrator

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

xray_recorder.configure(service="StaxOrchestrator:DeleteWorkload")
patch_all()


def lambda_handler(event: dict, _) -> dict:
    """Delete Stax Workloads Lambda Handler"""
    return StaxOrchestrator().delete_workload(**event)
