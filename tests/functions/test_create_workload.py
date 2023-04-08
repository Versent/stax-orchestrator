import pytest

from functions.create_workload.app import lambda_handler


class TestCreateWorkloadLambda:
    event: dict = {"workload_name": "some-workload-name"}

    def test_create_workload_lambda_workload_exists_error(self, mocker):
        # mock
        stax_orchestrator_mock = mocker.patch("functions.create_workload.app.StaxOrchestrator")
        stax_orchestrator_mock.return_value.workload_with_name_already_exists.return_value = True

        # test
        with pytest.raises(Exception):
            lambda_handler(self.event, {})

        stax_orchestrator_mock.assert_called_once()

    def test_create_workload_lambda_success(self, mocker):
        # mock
        stax_orchestrator_mock = mocker.patch("functions.create_workload.app.StaxOrchestrator")
        stax_orchestrator_mock.return_value.workload_with_name_already_exists.return_value = False

        # test
        assert lambda_handler(self.event, {}) == stax_orchestrator_mock.return_value.create_workload.return_value

        stax_orchestrator_mock.assert_called_once()
