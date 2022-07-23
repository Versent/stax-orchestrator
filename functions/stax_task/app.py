import logging
from os import environ
logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))
from staxapp.config import Config
from staxapp.openapi import StaxClient
from aws_lambda_powertools.utilities import parameters
from feedback.app import Stepfunction
Config.access_key = parameters.SSMProvider().get(name="/orchestrator/access_key", max_age=360, decrypt=True)
Config.secret_key = parameters.SSMProvider().get(name="/orchestrator/secret_key", max_age=360, decrypt=True)

def lambda_handler(event, context) -> dict:

    stax_task = StaxClient("tasks")
    task_status = stax_task.ReadTask(task_id=event["task_id"])
    logging.debug(f"task_status: {task_status}")
    event["task_status"] = task_status

    Stepfunction().send_heartbeats(
        event.get("callback_tokens", [])
    )


    return event

if __name__ == "__main__":
    lambda_handler({"task_id": "123"}, None)
