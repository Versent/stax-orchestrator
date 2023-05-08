import boto3

def create_ssm_parameter(ssm_client: boto3.client, name: str, value: str, type: str) -> None:
    """Create a SSM Parameter

    Args:
        ssm_client (str): Boto3 SSM client
        name (str): Name of the SSM Parameter
        value (str): Value to associate with the SSM Parameter
        type (str): Type of the SSM Parameter - valid values are 'String', 'StringList', 'SecureString'
    """
    ssm_client.put_parameter(
        Name=name,
        Value=value,
        Type=type,
        Overwrite=True
    )

def create_orchestrator_stax_parameters() -> None:
    """Creates required stax orchestrator SSM parameters
    """
    ssm_client = boto3.client('ssm')

    ssm_parameters = {
        "/orchestrator/stax/access/key": "", ## Fill
        "/orchestrator/stax/access/key/secret": "", ## Fill
        "/orchestrator/stax/artifact/bucket/name": "" ## Fill
    }

    # Create the orchestrator stax parameters
    for ssm_parameter_name, ssm_parameter_value in ssm_parameters.items():
        create_ssm_parameter(ssm_client, ssm_parameter_name, ssm_parameter_value, "SecureString")
        print("Successfully created SSM Parameter: ", ssm_parameter_name)

if __name__ == "__main__":
    create_orchestrator_stax_parameters()
