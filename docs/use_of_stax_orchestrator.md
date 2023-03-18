


## Stax Deployment Bucket

Inorder to use Stax to deploy workloads, we need to use s3 bucket accessible by Stax to store our artifacts, our cloudformation templates and package dependencies.

Stax has a workload `stax-deployment-bucket` manifest deployed in every installation that we can deploy to then start using the s3 bucket to store artifacts. Follow Stax's [guide](https://support.stax.io/hc/en-us/articles/4450989147919-Add-a-Workload-to-the-Workload-Catalog#:~:text=If%20you%20need%20to%20upload%20artifacts%20that%20are%20referenced%20by%20your%20Manifest%2C%20such%20as%20CloudFormation%20templates%2C%20you%20must%3A) to get started.

After you deploy the `stax-deployment-bucket` workload,

* Store the name of the bucket in a Ssm parameter with path `/orchestrator/stax/artifact/bucket/name` which will be consumed by Stax Orchestrator.
* Add a [policy](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-template-publishing-applications.html#:~:text=%7B%0A%20%20%20%20%22Version%22%3A%20%222012,aws%3ASourceAccount%22%3A%20%22123456789012%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%5D%0A%7D) to allow AWS's Serverless Service access the bucket to get artifacts.

## Deploying a workload

* Deploy a Stax workload [catalogue](https://support.stax.io/hc/en-us/articles/4450989147919-Add-a-Workload-to-the-Workload-Catalog).
    * Remember the Catalogue ID of the catalogue deployed as we will need this to deploy the workload.

* Run `Workload Step Function` step function with the following payload,
    ```
    {
        "aws_account_id": "asd12e3-7c0e-4807-96ee-asd12ec21r2",
        "aws_region": "ap-southeast-2",
        "operation": "deploy",
        "catalogue_id": "b3437e3b-55e3-4060-9dec-042f18dcf789",
        "catalogue_version_id": "69e4a16c-7c7c-48cf-bb8d-312c43fc0563",
        "workload_name": "orchestrator-stax-demo-vpc",
        "workload_parameters": {
            "Param1": "Value1"
        },
        "workload_tags": {
            "Tag1": "Value1"
        }
    }
    ```
    * aws_account_id - Stax AWS Account ID (UUID) to deploy workload to.
    * aws_region - The AWS Region to deploy the workload to.
    * catalogue_id - The ID of the catalogue containing workload manifest.
    * catalogue_version_id (OPTIONAL): Deploy a specific version of the catalogue workload.
    * workload_name - Name of the workload to deploy (must be unique).
    * workload_parameters - Parameters that get passed into cloudformation templates upon workload deployment.
    * workload_tags - Tags to attach to the workload.

## Updating a workload

* Update a Stax workload [catalogue](https://support.stax.io/hc/en-us/articles/4451005420943-Update-a-Workload).
    * Remember the Catalogue ID and version of the updated catalogue as we will need this to deploy the workload.

* Run `Workload Step Function` step function with the following payload,
    ```
    {
        "operation": "update",
        "workload_id": "b3437e3b-55e3-4060-9dec-042f18dcf789",
        "catalogue_version_id": "69e4a16c-7c7c-48cf-bb8d-312c43fc0563"
    }
    ```
    * workload_id - The ID of the workload to update
    * catalogue_version_id: The version of the catalogue workload to deploy

## Deleting a workload

* Run `Workload Step Function` step function with the following payload,
    ```
    {
        "operation": "delete",
        "workload_id": "b3437e3b-55e3-4060-9dec-042f18dcf789"
    }
    ```
    * workload_id - The ID of the workload to update
