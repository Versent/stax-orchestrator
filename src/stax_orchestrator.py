"""
    Common logic to interact with Stax to deploy workloads and monitor task status.
"""
import logging
from dataclasses import dataclass
from os import environ
from typing import Optional
from uuid import UUID, uuid4

import boto3
from aws_lambda_powertools.utilities import parameters
from aws_xray_sdk.core import patch_all, xray_recorder
from staxapp.config import Config as StaxConfig
from staxapp.openapi import StaxClient

logging.getLogger().setLevel(environ.get("LOG_LEVEL", logging.INFO))

xray_recorder.configure(service="StaxOrchestrator:Libs")
patch_all()


@dataclass(frozen=True, order=True)
class WorkloadEvent:
    """Event data containing required information to deploy a workload."""

    aws_account_id: int
    aws_region: str
    catalogue_id: UUID
    workload_name: str
    workload_parameters: Optional[dict] = None
    workload_tags: Optional[dict] = None


def get_stax_client(client_type: str) -> StaxClient:
    """Initialize and return stax client object
    Args:
        client_type (str): Type of stax client to instantiate (for e.g, workloads)
    """
    ssm_provider = parameters.SSMProvider()
    StaxConfig.access_key = ssm_provider.get(
        "/orchestrator/stax/access/key", max_age=21600, decrypt=True
    )
    StaxConfig.secret_key = ssm_provider.get(
        "/orchestrator/stax/access/key/secret", max_age=21600, decrypt=True
    )

    return StaxClient(client_type)


class MissingRequiredInput(Exception):
    """Raised when required user inputs are not present"""


@dataclass
class StaxOrchestrator:
    """Interact with Stax to deploy workloads and monitor workload task status."""

    workload_client: StaxClient = get_stax_client("workloads")
    tasks_client: StaxClient = get_stax_client("tasks")

    class TaskNotFound(Exception):
        """Raised when task not found in Stax"""

    class WorkloadWithNameAlreadyExists(Exception):
        """Raised when workload with same name already exists in Stax"""

    def get_catalogue_hash(self) -> str:
        """
        Generate a random hash for stax catalogue version
        """
        return uuid4().hex[:7]

    def create_catalogue(
        self,
        bucket_name: str,
        catalogue_name: str,
        cloudformation_manifest_path: str,
        description: Optional[str] = "",
    ) -> dict:
        """Create a Stax Catalogue with given cloudformation template

        Args:
            bucket_name (str): Name of the s3 bucket to upload the manifest to
            catalogue_name (str): Name of the catalogue to create
            cloudformation_manifest_path (str): Local path to the cloudformation manifest
            description (Optional[str], optional): Catalogue description. Defaults to "".
        """
        s3_resource = boto3.resource("s3")
        catalogue_version = self.get_catalogue_hash()
        cfn_name = f"{catalogue_version}-{catalogue_name}.yaml"
        s3_resource.Bucket(bucket_name).upload_file(
            cloudformation_manifest_path, cfn_name
        )

        manifest_body = f"""Resources:
        - WorkloadSSM:
            Type: AWS::Cloudformation
            TemplateURL: s3://{bucket_name}/{cfn_name}
        """
        return self.workload_client.CreateCatalogueItem(
            Name=catalogue_name,
            ManifestBody=manifest_body,
            Version=catalogue_version,
            Description=description,
        )

    # pylint: disable=too-many-arguments
    def create_workload(
        self,
        workload_name: str,
        catalogue_id: UUID,
        aws_region: str,
        aws_account_id: UUID,
        workload_parameters: Optional[list] = None,
        workload_tags: Optional[dict] = None,
    ) -> dict:
        """Create a Stax workload with given catalogue and workload information

        Args:
            workload_name (str): Name of the workload to create
            catalogue_id (UUID): Catalogue UUID to use to create the worload
            aws_region (str): The AWS Region to deploy the workload to
            aws_account_id (UUID): Stax AWS Account UUID to deploy the workload to
            workload_parameters (Optional[list], optional): Workload cloudformation parameters
            workload_tags (Optional[dict], optional): Tags to attach to the workload to be deployed
        """
        create_workload_payload = {
            "Name": workload_name,
            "CatalogueId": catalogue_id,
            "AccountId": aws_account_id,
            "Region": aws_region,
        }

        if workload_parameters:
            create_workload_payload["Parameters"] = self.get_parameters_list(
                workload_parameters
            )

        if workload_tags:
            create_workload_payload["Tags"] = workload_tags

        return self.workload_client.CreateWorkload(**create_workload_payload)

    def get_parameters_list(self, workload_parameters: dict) -> list:
        """Takes a dict of params/values and converts them into a list of dicts

        Args:
            workload_parameters (dict): Key/value pair of workload cloudformation parameters

        Returns:
            list: List of dictionaries containing workload cloudformation parameters
        """
        parameters_list = []
        for key, value in workload_parameters.items():
            parameters_list.append({"Key": key, "Value": value})
        return parameters_list

    def get_task_status(self, task_id: UUID) -> dict:
        """Poll Stax to get status of a given task

        Args:
            task_id (UUID): ID of the task to get status for

        Returns:
            dict: Task status information
        """
        return self.tasks_client.ReadTask(task_id=task_id)

    def get_workloads(self) -> dict:
        """Poll Stax to get a list of all workloads

        Returns:
            dict: Dictionary containing lists of workloads.
        """
        return self.workload_client.ReadWorkloads()

    def delete_workload(self, workload_id: UUID) -> dict:
        """Delete a Stax workload

        Args:
            workload_id (UUID): ID of the workload to delete

        Returns:
            dict: Delete workload response
        """
        return self.workload_client.DeleteWorkload(workload_id=workload_id)

    def update_workload(self, workload_id: UUID, catalogue_version_id: UUID) -> dict:
        """Update a Stax workload

        Args:
            workload_id (UUID): ID of the workload to update
            catalogue_version_id (UUID): The version to update the workload to.

        Returns:
            dict: Update workload response
        """
        return self.workload_client.UpdateWorkload(
            workload_id=workload_id, catalogue_version_id=catalogue_version_id
        )

    def workload_with_name_already_exists(self, workload_name: str) -> bool:
        """Check if a workload with the same name already exists in Stax

        Args:
            workload_name (str): Name of the Stax workload

        Returns:
            bool: True if workload with the same name already exists else False
        """
        workloads = self.get_workloads()

        for workload in workloads["Workloads"]:
            if workload["Name"] == workload_name and workload["Status"] == "ACTIVE":
                return True

        return False
