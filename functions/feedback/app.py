import logging
from os import environ

import boto3
logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))



class Stepfunction:
    """Opinionated way to interact with Stepfunctions
    """

    arn: str = ""
    states_client = boto3.client("stepfunctions")

    def __init__(self, arn=None, states_client=None) -> None:
        self.arn = arn
        self.states_client = states_client

    def setup_client(self):
        self.states_client = boto3.client("stepfunctions")

    def send_heartbeats(self, callback_tokens: list ):
        if self.states_client is None:
            self.setup_client()

        for token in callback_tokens:
            try:

                self.states_client.send_task_heartbeat(
                    taskToken=token
                )
                logging.debug(f"{token} heartbeat sent correctly")
            except self.states_client.exceptions.TaskTimedOut:
                logging.warning(f"{token} task timed out")
        return True






def lambda_handler(event, context) -> dict:
    # do a thing


    return event
