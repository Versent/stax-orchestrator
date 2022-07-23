import logging
from os import environ
logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

def lambda_handler(event, context) -> dict:
    if "task_id" not in event:
        raise Exception("task_id is required")
    if "send_heartbeats" in event and not isinstance(event["send_heartbeats"], list):
        raise Exception("send_heartbeats must be a list")


    return event
