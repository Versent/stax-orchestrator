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


class WorkloadOperation(Enum):
    DEPLOY = "deploy"
    UPDATE = "update"


@dataclass(frozen=True, order=True)
class WorkloadEvent:
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
    StaxConfig.access_key = ssm_provider.get("/orchestrator/stax/access/key", max_age=21600, decrypt=True)
    StaxConfig.secret_key = ssm_provider.get("/orchestrator/stax/access/key/secret", max_age=21600, decrypt=True)

    return StaxClient(client_type)


class MissingRequiredInput(Exception):
    """Raised when required user inputs are not present"""


@dataclass
class StaxOrchestrator:

    workload_client: StaxClient = get_stax_client("workloads")
    tasks_client: StaxClient = get_stax_client("tasks")

    class TaskNotFound(Exception):
        """Raised when task not found in Stax"""

    class WorkloadWithNameAlreadyExists(Exception):
        """Raised when workload with same name already exists in Stax"""

    def get_catalogue_hash(self) -> str:
        return uuid4().hex[:7]

    def create_catalogue(
        self,
        bucket: str,
        catalogue_name: str,
        cloudformation_manifest_path: str,
        description: Optional[str] = "",
    ) -> dict:
        s3 = boto3.resource("s3")
        catalogue_version = self.get_catalogue_hash()
        cfn_name = f"{catalogue_version}-{catalogue_name}.yaml"
        s3.Bucket(bucket).upload_file(cloudformation_manifest_path, cfn_name)

        manifest_body = f"""Resources:
        - WorkloadSSM:
            Type: AWS::Cloudformation
            TemplateURL: s3://{bucket}/{cfn_name}
        """
        return self.workload_client.CreateCatalogueItem(
            Name=catalogue_name,
            ManifestBody=manifest_body,
            Version=catalogue_version,
            Description=description,
        )

    def create_workload(
        self,
        workload_name: str,
        catalogue_id: str,
        aws_region: str,
        aws_account_id: str,
        workload_parameters: Optional[list] = None,
        workload_tags: Optional[dict] = None,
    ) -> dict:
        create_workload_payload = {
            "Name": workload_name,
            "CatalogueId": catalogue_id,
            "AccountId": aws_account_id,
            "Region": aws_region,
        }

        if workload_parameters:
            create_workload_payload["Parameters"] = self.get_parameters_dict(workload_parameters)

        if workload_tags:
            create_workload_payload["Tags"] = workload_tags

        return self.workload_client.CreateWorkload(**create_workload_payload)

    def get_parameters_dict(self, workload_parameters: dict) -> list:
        parameters_list = []
        for key, value in workload_parameters.items():
            parameters_list.append({"Key": key, "Value": value})
        return parameters_list

    def get_task_status(self, task_id: UUID) -> dict:
        return self.tasks_client.ReadTask(task_id=task_id)

    def get_workloads(self) -> dict:
        return self.workload_client.ReadWorkloads()

    def delete_workload(self, workload_id: UUID) -> dict:
        return self.workload_client.DeleteWorkload(workload_id=workload_id)

    def update_workload(self, workload_id: UUID, catalogue_version_id: UUID) -> dict:
        return self.workload_client.UpdateWorkload(workload_id=workload_id, catalogue_version_id=catalogue_version_id)

    def does_workload_with_name_already_exist(self, workload_name: str) -> bool:
        workloads = self.get_workloads()

        for workload in workloads["Workloads"]:
            if workload["Name"] == workload_name and workload["Status"] == "ACTIVE":
                return True

        return False
