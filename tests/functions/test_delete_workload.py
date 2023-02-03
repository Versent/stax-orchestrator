from functions.delete_workload.app import lambda_handler


class TestDeleteWorkloadLambda:
    event: dict = {"workload_name": "some-workload-name"}

    def test_delete_workload_lambda(self, mocker):
        # mock
        stax_orchestrator_mock = mocker.patch("functions.delete_workload.app.StaxOrchestrator")

        # test
        assert lambda_handler(self.event, {}) == stax_orchestrator_mock.return_value.delete_workload.return_value

        stax_orchestrator_mock.return_value.delete_workload.assert_called_once_with(**self.event)
