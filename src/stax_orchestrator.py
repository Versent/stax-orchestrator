"""
    Common logic to interact with Stax to deploy/update/delete workloads and monitor task status.
"""
import logging
from dataclasses import dataclass
from enum import Enum
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


@dataclass
class StaxOrchestrator:
    """Interact with Stax to deploy workloads and monitor workload task status."""

    workload_client: StaxClient = get_stax_client("workloads")
    tasks_client: StaxClient = get_stax_client("tasks")

    @dataclass(frozen=True)
    class CreateWorkloadEvent:
        """Event data containing required information to deploy a workload."""

        aws_account_id: UUID
        aws_region: str
        catalogue_id: UUID
        workload_name: str
        catalogue_version_id: Optional[UUID] = None
        workload_parameters: Optional[dict] = None
        workload_tags: Optional[dict] = None

    @dataclass(frozen=True)
    class DeleteWorkloadEvent:
        """Event data containing required information to delete a workload."""

        workload_id: UUID

    @dataclass(frozen=True)
    class UpdateWorkloadEvent:
        """Event data containing required information to update a workload."""

        workload_id: UUID
        catalogue_version_id: UUID

    class WorkloadOperation(str, Enum):
        """Supported workload operations"""

        DEPLOY = "deploy"
        UPDATE = "update"
        DELETE = "delete"

    class WorkloadWithNameAlreadyExists(Exception):
        """Raised when workload with same name already exists in Stax"""

    class MissingRequiredInput(Exception):
        """Raised when required user inputs are not present"""

    class WorkloadOperationNotSupported(Exception):
        """Raised when workload operation is not one of deploy/update/delete"""

    # pylint: disable=too-many-arguments
    def create_update_catalogue(
        self,
        bucket_name: str,
        catalogue_name: str,
        cloudformation_manifest_path: str,
        description: str,
        update_catalogue: bool = False,
        catalogue_id: UUID = None,
    ) -> dict:
        """Creates/Updates a Stax Catalogue with given cloudformation template

        Args:
            bucket_name (str): Name of the s3 bucket to upload the manifest to
            catalogue_name (str): Name of the catalogue to create
            cloudformation_manifest_path (str): Local path to the cloudformation manifest
            description (str): Catalogue description
            update_catalogue (Optional[bool]): True if updating catalogue version.
            catalogue_id (UUID): ID of the catalogue if updating.
        """
        s3_resource = boto3.resource("s3")
        catalogue_version = str(uuid4())
        cfn_name = f"{catalogue_version}-{catalogue_name}.yaml"
        s3_resource.Bucket(bucket_name).upload_file(
            cloudformation_manifest_path, cfn_name
        )

        manifest_body = f"""Resources:
        - WorkloadSSM:
            Type: AWS::Cloudformation
            TemplateURL: s3://{bucket_name}/{cfn_name}
        """
        if update_catalogue:
            return self.workload_client.CreateCatalogueVersion(
                ManifestBody=manifest_body,
                Version=catalogue_version,
                Description=description,
                catalogue_id=catalogue_id,
            )

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
        catalogue_version_id: UUID = None,
        workload_parameters: Optional[list] = None,
        workload_tags: Optional[dict] = None,
    ) -> dict:
        """Create a Stax workload with given catalogue and workload information

        Args:
            workload_name (str): Name of the workload to create
            catalogue_id (UUID): Catalogue UUID to use to create the worload
            aws_region (str): The AWS Region to deploy the workload to
            aws_account_id (UUID): Stax AWS Account UUID to deploy the workload to
            catalogue_version_id (Optional[str]): Deploy a certain version of the catalogue
            workload_parameters (Optional[list], optional): Workload cloudformation parameters
            workload_tags (Optional[dict], optional): Tags to attach to the workload to be deployed
        """
        create_workload_payload = {
            "Name": workload_name,
            "CatalogueId": catalogue_id,
            "AccountId": aws_account_id,
            "Region": aws_region,
        }

        if catalogue_version_id:
            create_workload_payload["CatalogueVersionId"] = catalogue_version_id

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

    def get_deploy_workload_kwargs(self, event: dict) -> dict:
        """Get required workload arguments from the event for deploy operation

        Args:
            event (dict): Details about the workload to be deployed

        Returns:
            dict: Dictionary of deploy workload keyword arguments.
        """
        workload_kwargs = {
            "aws_account_id": event["aws_account_id"],
            "aws_region": event["aws_region"],
            "catalogue_id": event["catalogue_id"],
            "workload_name": event["workload_name"],
        }

        if "catalogue_version_id" in event:
            workload_kwargs["catalogue_version_id"] = event["catalogue_version_id"]

        if "workload_parameters" in event:
            workload_kwargs["workload_parameters"] = event["workload_parameters"]

        if "workload_tags" in event:
            workload_kwargs["workload_tags"] = event["workload_tags"]

        return workload_kwargs

    def get_update_workload_kwargs(self, event: dict) -> dict:
        """Get required workload arguments from the event for an update operation

        Args:
            event (dict): Details about the workload to be updated

        Returns:
            dict: Dictionary of update workload keyword arguments.
        """
        return {
            "catalogue_version_id": event["catalogue_version_id"],
            "workload_id": event["workload_id"],
        }

    def get_delete_workload_kwargs(self, event: dict) -> dict:
        """Get required workload arguments from the event for a delete operation

        Args:
            event (dict): Details about the workload to be deleted

        Returns:
            dict: Dictionary of update workload keyword arguments.
        """
        return {"workload_id": event["workload_id"]}
