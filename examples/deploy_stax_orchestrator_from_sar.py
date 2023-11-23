import boto3
import argparse
from typing import Dict, Any


def get_aws_account_id() -> str:
    """
    Get the current AWS account ID.

    Returns:
    - str: AWS account ID
    """
    sts_client = boto3.client("sts")
    return sts_client.get_caller_identity()["Account"]


def get_application_details() -> Dict[str, Any]:
    """
    Get details of the Stax Orchestrator application from the Serverless Application Repository.

    Returns:
    - dict: Serverless Application details
    """
    aws_account_id = get_aws_account_id()
    sar_client = boto3.client("serverlessrepo")
    application_id = f"arn:aws:serverlessrepo:ap-southeast-2:{aws_account_id}:applications/stax-orchestrator"
    return sar_client.get_application(ApplicationId=application_id)


def create_cloudformation_change_set(
    app_id: str, semantic_version: str, stack_name: str, cfn_parameters: Dict[str, Any]
) -> str:
    """
    Create a CloudFormation change set for the Stax Orchestrator application.

    Parameters:
    - app_id (str): Application ID
    - semantic_version (str): Semantic version of the application
    - stack_name (str): CloudFormation stack name
    - cfn_parameters (dict): CloudFormation parameters

    Returns:
    - str: Change set ID
    """
    serverlessrepo_client = boto3.client("serverlessrepo")
    return serverlessrepo_client.create_cloud_formation_change_set(
        ApplicationId=app_id,
        Capabilities=["CAPABILITY_IAM", "CAPABILITY_RESOURCE_POLICY"],
        SemanticVersion=semantic_version,
        StackName=stack_name,
        ParameterOverrides=[{"Name": key, "Value": value} for key, value in cfn_parameters.items()],
    )["ChangeSetId"]


def execute_change_set(change_set_id: str, stack_name: str) -> None:
    """
    Execute a CloudFormation change set.

    Parameters:
    - change_set_id (str): Change set ID
    - stack_name (str): CloudFormation stack name

    Returns:
    - None
    """
    cloudformation_client = boto3.client("cloudformation")
    cloudformation_client.execute_change_set(
        ChangeSetName=change_set_id,
        StackName=stack_name,
    )


def deploy_stax_orchestrator(cfn_parameters: Dict[str, Any]) -> None:
    """
    Deploy a Stax Orchestrator from Serverless Application Repository.

    Parameters:
    - cfn_parameters (dict): A dictionary containing parameter values for the application.

    Returns:
    - None
    """
    stack_name = "orchestrator-stax"
    app_details = get_application_details()

    print(f"Deploying version {app_details['Version']['SemanticVersion']} of the application.")

    change_set_id = create_cloudformation_change_set(
        app_details["ApplicationId"], app_details["Version"]["SemanticVersion"], stack_name, cfn_parameters
    )

    # Wait for change set to be created
    waiter = boto3.client("cloudformation").get_waiter("change_set_create_complete")

    try:
        waiter.wait(
            ChangeSetName=change_set_id,
            WaiterConfig={
                "Delay": 5,
                "MaxAttempts": 30,
            },
        )

        # Execute the change set
        execute_change_set(change_set_id, f"serverlessrepo-{stack_name}")

        # Wait for stack to be created
        waiter = boto3.client("cloudformation").get_waiter("stack_create_complete")
        waiter.wait(
            StackName=f"serverlessrepo-{stack_name}",
            WaiterConfig={
                "Delay": 5,
                "MaxAttempts": 30,
            },
        )

    except Exception as waiter_exception:
        print("An error occurred while waiting for the change set to be created: %s", waiter_exception)

    print(f"Successfully deployed Stax Orchestrator version {app_details['Version']['SemanticVersion']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--deploy-workload-state-machine",
        help="Specify 'true' if you would like to deploy workload state machine",
        required=False,
        type=str,
        default="false",
        choices=["true", "false"],
    )
    parser.add_argument(
        "--deploy-workload-dashboard",
        help="Specify 'true' if you would like to deploy workload state machine cloudwatch dashboard",
        required=False,
        type=str,
        default="false",
        choices=["true", "false"],
    )
    parser.add_argument(
        "--deploy-task-watcher-dashboard",
        help="Specify 'true' if you would like to deploy task watcher state machine cloudwatch dashboard",
        required=False,
        type=str,
        default="false",
        choices=["true", "false"],
    )
    parser.add_argument(
        "--lambda-log-group-retention",
        help="Specify the number of days to retain the lambda log groups",
        required=False,
        type=str,
        default="60",
    )
    parser.add_argument(
        "--enable-state-machine-tracing",
        help="Specify 'true' if you would like to X-Ray tracing enabled for State Machines",
        required=False,
        type=str,
        default="false",
        choices=["true", "false"],
    )
    parser.add_argument(
        "--enable-lambda-tracing",
        help="Specify 'true' if you would like to X-Ray tracing enabled for AWS Lambdas",
        required=False,
        type=str,
        default="false",
        choices=["true", "false"],
    )
    parser.add_argument(
        "--enable-alerting",
        help="Specify 'true' if you would like enable alerting for Stax Orchestrator application. Also set --alerts-https-endpoint if alerting is enabled",
        required=False,
        type=str,
        default="false",
        choices=["true", "false"],
    )
    parser.add_argument(
        "--alerts-https-endpoint",
        help="Specify the HTTPS endpoint to send alerts to. Specify HTTPS endpoint or an EMAIL to send alerts to if --enable-alerting is set to True",
        required=False,
        type=str,
        default="",
    )
    parser.add_argument(
        "--alerts-email-endpoint",
        help="Specify the EMAIL endpoint to send alerts to. Specify HTTPS endpoint or an EMAIL to send alerts to if --enable-alerting is set to True",
        required=False,
        type=str,
        default="",
    )
    parser.add_argument(
        "--python-logging-level",
        help="Specify the python logging level for the lambda functions",
        required=False,
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    args = parser.parse_args()
    parameters = {
        "DeployWorkloadStateMachine": args.deploy_workload_state_machine,
        "DeployWorkloadCloudwatchDashboard": args.deploy_workload_dashboard,
        "DeployTaskWatcherCloudwatchDashboard": args.deploy_task_watcher_dashboard,
        "LambdaLogGroupRetentionInDays": args.lambda_log_group_retention,
        "EnableStateMachineTracing": args.enable_state_machine_tracing,
        "EnableLambdaTracing": args.enable_lambda_tracing,
        "EnableAlerting": args.enable_alerting,
        "AlertsHttpsEndpoint": args.alerts_https_endpoint,
        "AlertsEmail": args.alerts_email_endpoint,
        "PythonLoggingLevel": args.python_logging_level,
    }

    deploy_stax_orchestrator(parameters)
