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

    workload_client: StaxClient = get_stax_client("workloads")
    tasks_client: StaxClient = get_stax_client("tasks")

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
        workload_parameters: list = None,
        workload_tags: dict = None,
    ) -> dict:
        workload_parameters = self.get_parameters_dict(workload_parameters)

        return self.workload_client.CreateWorkload(
            Name=workload_name,
            CatalogueId=catalogue_id,
            AccountId=aws_account_id,
            Region=aws_region,
            Parameters=workload_parameters,
            Tags=workload_tags,
        )

    def get_parameters_dict(self, workload_parameters: dict) -> list:
        parameters_list = []
        for key, value in workload_parameters.items():
            parameters_list.append({"Key": key, "Value": value})
        return parameters_list

    def get_task_status(self, task_id: UUID) -> str:
        return self.tasks_client.ReadTask(task_id=task_id)

    def get_workloads(self):
        return self.workload_client.ReadWorkloads()

    def update_workload(self, workload_id: UUID, catalogue_version_id: UUID):
        return self.workload_client.UpdateWorkload(
            workload_id=workload_id, catalogue_version_id=catalogue_version_id
        )
