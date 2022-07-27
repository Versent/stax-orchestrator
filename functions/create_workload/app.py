import logging
from os import environ

from stax_orchestrator import StaxOrchestrator

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))


def lambda_handler(event, _) -> dict:
    """Create Stax Workloads Lambda Handler"""
    stax_orchestrator = StaxOrchestrator()
    event["create_workload_response"] = stax_orchestrator.create_workload(
        **event["workload_payload"]
    )

    return event
