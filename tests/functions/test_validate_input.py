import pytest

from functions.validate_input.app import lambda_handler


class TestValidateInputLambda:
    def test_validate_input_workload_create(self, mocker):
        # data
        event: dict = {"operation": "create"}

        # mock
        stax_orchestrator_mock = mocker.patch("functions.validate_input.app.StaxOrchestrator")

        # test
        assert (
            lambda_handler(event, {}) == stax_orchestrator_mock.return_value.CreateWorkloadEvent.return_value.__dict__
        )

        stax_orchestrator_mock.return_value.get_create_workload_kwargs.assert_called_once_with(event)
        stax_orchestrator_mock.return_value.CreateWorkloadEvent.assert_called_once_with(
            **stax_orchestrator_mock.return_value.get_create_workload_kwargs.return_value
        )

    def test_validate_input_workload_update(self, mocker):
        # data
        event: dict = {"operation": "update"}

        # mock
        stax_orchestrator_mock = mocker.patch("functions.validate_input.app.StaxOrchestrator")

        # test
        assert (
            lambda_handler(event, {}) == stax_orchestrator_mock.return_value.UpdateWorkloadEvent.return_value.__dict__
        )

        stax_orchestrator_mock.return_value.get_update_workload_kwargs.assert_called_once_with(event)
        stax_orchestrator_mock.return_value.UpdateWorkloadEvent.assert_called_once_with(
            **stax_orchestrator_mock.return_value.get_update_workload_kwargs.return_value
        )

    def test_validate_input_workload_delete(self, mocker):
        # data
        event: dict = {"operation": "delete"}

        # mock
        stax_orchestrator_mock = mocker.patch("functions.validate_input.app.StaxOrchestrator")

        # test
        assert (
            lambda_handler(event, {}) == stax_orchestrator_mock.return_value.DeleteWorkloadEvent.return_value.__dict__
        )

        stax_orchestrator_mock.return_value.get_delete_workload_kwargs.assert_called_once_with(event)
        stax_orchestrator_mock.return_value.DeleteWorkloadEvent.assert_called_once_with(
            **stax_orchestrator_mock.return_value.get_delete_workload_kwargs.return_value
        )

    def test_validate_input_workload_value_error(self, mocker):
        # data
        event: dict = {"operation": "unsupported-operation"}

        # mock
        mocker.patch("functions.validate_input.app.StaxOrchestrator")

        # test
        with pytest.raises(ValueError):
            lambda_handler(event, {})
