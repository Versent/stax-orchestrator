
from json import dumps
from src.stax_orchestrator import StaxOrchestrator

stax_orchestrator = StaxOrchestrator()

bucket = "s3_bucket_name"
catalogue_name = "simple-dynamodb"
cloudformation_manifest_path = "sample-workload-templates/dynamo.json"
description = "Dynamodb table for business needs"
catalogue_id = "id_of_catalogue_to_update"

update_catalogue_response = stax_orchestrator.deploy_catalogue(bucket, catalogue_name, cloudformation_manifest_path, description, catalogue_id, new_catalogue_version=True)

print(dumps(update_catalogue_response, indent=4, sort_keys=True))
