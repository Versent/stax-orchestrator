from src.stax_orchestrator import StaxOrchestrator, get_stax_client


class TestStaxOrchestrator:
    bucket = "orchestrator-stax-bucket"
    workload_name = "simple-dynamodb-workload"
    workload_id = "some-workload-id"
    catalogue_id = "some-cat-id"
    aws_region = "some-aws-region"
    aws_account_id = "some-aws-account-id"
    catalogue_name = "simple-dynamodb"
    cloudformation_manifest_path = "cloudformation/dynamo.json"
    workload_parameters = {"workload-param1": "some-value1"}
    description = "Create a dynamodb workload"
    catalogue_version_id = "some-catalogue-version-id"

    def test_get_task_status(self, get_stax_client_mock, mocker):
        stax_orchestrator = StaxOrchestrator()

        # test
        exec_result = stax_orchestrator.get_task_status("some-id")

        # validate
        get_stax_client_mock.assert_called_once_with("tasks")
        assert exec_result == get_stax_client_mock.return_value.ReadTask.return_value

    def test_create_catalogue_item(self, mocker):
        # mock
        boto3_mock = mocker.patch("src.stax_orchestrator.boto3")
        uuid_mock = mocker.patch("src.stax_orchestrator.uuid4")
        stax_orchestrator = StaxOrchestrator()

        # test
        assert (
            stax_orchestrator.create_catalogue(
                self.bucket, self.catalogue_name, self.cloudformation_manifest_path, self.description
            )
            == stax_orchestrator.workload_client.CreateCatalogueItem.return_value
        )
        boto3_mock.resource.return_value.Bucket.assert_called_once_with(self.bucket)
        boto3_mock.resource.return_value.Bucket.return_value.upload_file.assert_called_once_with(
            self.cloudformation_manifest_path, f"{str(uuid_mock.return_value)}-{self.catalogue_name}.yaml"
        )

    def test_create_catalogue_version(self, mocker):
        # mock
        boto3_mock = mocker.patch("src.stax_orchestrator.boto3")
        uuid_mock = mocker.patch("src.stax_orchestrator.uuid4")
        stax_orchestrator = StaxOrchestrator()

        # test
        assert (
            stax_orchestrator.create_catalogue(
                self.bucket,
                self.catalogue_name,
                self.cloudformation_manifest_path,
                self.description,
                "some-catalogue_id",
            )
            == stax_orchestrator.workload_client.CreateCatalogueVersion.return_value
        )
        boto3_mock.resource.return_value.Bucket.assert_called_once_with(self.bucket)
        boto3_mock.resource.return_value.Bucket.return_value.upload_file.assert_called_once_with(
            self.cloudformation_manifest_path, f"{str(uuid_mock.return_value)}-{self.catalogue_name}.yaml"
        )

    def test_create_workload(self, mocker):
        # mock
        get_parameters_list_mock = mocker.patch.object(StaxOrchestrator, "get_parameters_list")
        stax_orchestrator = StaxOrchestrator()

        workload_tags = {"workload-tag1": "some-value1"}

        workload_params = {
            "Name": self.workload_name,
            "CatalogueId": self.catalogue_id,
            "AccountId": self.aws_account_id,
            "Region": self.aws_region,
            "CatalogueVersionId": self.catalogue_version_id,
            "Parameters": get_parameters_list_mock.return_value,
            "Tags": workload_tags,
        }

        # test
        assert (
            stax_orchestrator.create_workload(
                self.workload_name,
                self.catalogue_id,
                self.aws_region,
                self.aws_account_id,
                self.catalogue_version_id,
                self.workload_parameters,
                workload_tags,
            )
            == stax_orchestrator.workload_client.CreateWorkload.return_value
        )
        stax_orchestrator.workload_client.CreateWorkload.assert_called_once_with(**workload_params)
        get_parameters_list_mock.assert_called_once_with(self.workload_parameters)

    def test_get_parameters_list(self):
        stax_orchestrator = StaxOrchestrator()

        expected_response = [{"Key": "workload-param1", "Value": "some-value1"}]

        # test
        assert stax_orchestrator.get_parameters_list(self.workload_parameters) == expected_response

    def test_get_workloads(self):
        stax_orchestrator = StaxOrchestrator()

        # test
        assert stax_orchestrator.get_workloads() == stax_orchestrator.workload_client.ReadWorkloads.return_value

    def test_delete_workload(self):
        stax_orchestrator = StaxOrchestrator()

        # test
        assert (
            stax_orchestrator.delete_workload(self.workload_id)
            == stax_orchestrator.workload_client.DeleteWorkload.return_value
        )
        stax_orchestrator.workload_client.DeleteWorkload.assert_called_once_with(workload_id=self.workload_id)

    def test_update_workload(self):
        stax_orchestrator = StaxOrchestrator()

        # test
        assert (
            stax_orchestrator.update_workload(self.workload_id, self.catalogue_version_id)
            == stax_orchestrator.workload_client.UpdateWorkload.return_value
        )
        stax_orchestrator.workload_client.UpdateWorkload.assert_called_once_with(
            workload_id=self.workload_id, CatalogueVersionId=self.catalogue_version_id
        )

    def test_workload_with_name_already_exists_true(self, mocker):
        # mock
        get_workloads_mock = mocker.patch.object(StaxOrchestrator, "get_workloads")
        get_workloads_mock.return_value = {"Workloads": [{"Name": "existing-workload", "Status": "ACTIVE"}]}

        stax_orchestrator = StaxOrchestrator()

        # test
        assert stax_orchestrator.workload_with_name_already_exists("existing-workload") == True

    def test_workload_with_name_already_exists_false(self, mocker):
        # mock
        get_workloads_mock = mocker.patch.object(StaxOrchestrator, "get_workloads")
        get_workloads_mock.return_value = {"Workloads": [{"Name": "some-workload", "Status": "ACTIVE"}]}

        stax_orchestrator = StaxOrchestrator()

        # test
        assert stax_orchestrator.workload_with_name_already_exists("non-existent-workload") == False

    def test_get_create_workload_kwargs(self):
        stax_orchestrator = StaxOrchestrator()

        # data
        event = {
            "aws_account_id": self.aws_account_id,
            "aws_region": self.aws_region,
            "catalogue_id": self.catalogue_id,
            "workload_name": self.workload_name,
            "catalogue_version_id": self.catalogue_version_id,
            "workload_id": None,
        }

        expected_response = {
            "aws_account_id": self.aws_account_id,
            "aws_region": self.aws_region,
            "catalogue_id": self.catalogue_id,
            "workload_name": self.workload_name,
            "catalogue_version_id": self.catalogue_version_id,
        }

        # test
        exec_result = stax_orchestrator.get_create_workload_kwargs(event)
        assert exec_result == expected_response
        assert "workload_id" not in exec_result

    def test_get_update_workload_kwargs(self):
        stax_orchestrator = StaxOrchestrator()

        # data
        event_and_response = {"catalogue_version_id": self.catalogue_version_id, "workload_id": self.workload_id}

        # test
        assert stax_orchestrator.get_update_workload_kwargs(event_and_response) == event_and_response

    def test_get_delete_workload_kwargs(self):
        stax_orchestrator = StaxOrchestrator()

        # data
        event_and_response = {"workload_id": self.workload_id}

        # test
        assert stax_orchestrator.get_delete_workload_kwargs(event_and_response) == event_and_response


class TestStaxClient:
    def test_get_stax_client(self, mocker):
        stax_client_mock = mocker.patch("src.stax_orchestrator.StaxClient")
        parameters_mock = mocker.patch("src.stax_orchestrator.parameters")

        # test
        assert get_stax_client("workloads") == stax_client_mock.return_value
        parameters_mock.SSMProvider.return_value.assert_has_calls(
            [
                mocker.call.get("/orchestrator/stax/access/key", max_age=21600, decrypt=True),
                mocker.call.get("/orchestrator/stax/access/key/secret", max_age=21600, decrypt=True),
            ]
        )
