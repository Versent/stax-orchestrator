from functions.update_workload.app import lambda_handler


class TestUpdateWorkloadLambda:
    event: dict = {"workload_name": "some-workload-name"}

    def test_update_workload_lambda(self, mocker):
        # mock
        stax_orchestrator_mock = mocker.patch("functions.update_workload.app.StaxOrchestrator")

        # test
        assert lambda_handler(self.event, {}) == stax_orchestrator_mock.return_value.update_workload.return_value

        stax_orchestrator_mock.return_value.update_workload.assert_called_once_with(**self.event)
