import logging
from os import environ

import boto3
from staxapp.config import Config as StaxConfig
from staxapp.openapi import StaxClient

logging.getLogger().setLevel(environ.get("LOGLEVEL", logging.INFO))

def get_stax_client(client_type):
    """Initialize and return stax client object

    Args:
        client_type (str): Type of stax client to instantiate (for e.g, workloads)
    """
    StaxConfig.access_key = get_ssm_parameter("/orchestrator/stax/access/key")
    StaxConfig.secret_key = get_ssm_parameter("/orchestrator/stax/access/key/secret")

    return StaxClient(client_type)

def get_ssm_parameter(paramter_path, boto_client=None):
    """Fetch parameters from Systems Manager Parameter Store

    Args:
        parameter_path (str): The complete SSM parameter path to fetch the value from (e.g., /stax/lambda/function/arn)
        boto_client (object, optional): Boto3 client to use to fetch the parameter, useful when fetching cross account parameters.
    """
    if not boto_client:
        boto_client = boto3.client('ssm')

    try:
        response = boto_client.get_parameter(Name=paramter_path, WithDecryption=True)
        return response['Parameter']['Value']
    except (boto_client.exceptions.ParameterNotFound, KeyError):
        raise ValueError(f'Unable to fetch ssm parameter {paramter_path}')

def put_parameter(parameter_path, parameter_value, boto_client=None, description=None, secure_string=False):
    """Populate ssm parameter with the given value in the authenticated account.

    Args:
        parameter_path (str): SSM parameter key
        parameter_value (str): SSM parameter value
        boto_client (object, optional): Boto3 client to use to create the parameter
        description (str, optional): Description to include with the parameter
        secure_string (bool, optional): Store the value of the parameter as secure string if True
    """
    if not boto_client:
        boto_client = boto3.client('ssm')
    try:
        parameter_kwargs = {
            "Name": parameter_path,
            "Value": parameter_value,
            "Type": "String",
            "Overwrite": True,
            "Description": description,
        }

        if secure_string:
            parameter_kwargs["Type"] = "SecureString"

        boto_client.put_parameter(**parameter_kwargs)

    except boto_client.exceptions.ClientError as client_error:
        logging.error("Client error occured whilst trying to put ssm parameter: %s", client_error)
        raise
