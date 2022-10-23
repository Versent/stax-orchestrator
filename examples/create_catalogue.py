
from json import dumps
from src.stax_orchestrator import StaxOrchestrator

stax_orchestrator = StaxOrchestrator()

bucket = "s3_bucket_name"
catalogue_name = "simple-dynamodb"
cloudformation_manifest_path = "sample-workload-templates/dynamo.json"
description = "Dynamodb table for business needs"

deploy_catalogue_response = stax_orchestrator.deploy_catalogue(bucket, catalogue_name, cloudformation_manifest_path, description)

print(dumps(deploy_catalogue_response, indent=4, sort_keys=True))
