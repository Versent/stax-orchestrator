from functions.get_task_status.app import lambda_handler


class TestGetTaskStatusLambda:
    def test_get_task_status(self, mocker):
        # data
        event: dict = {"task_id": "some-task-id"}

        # mock
        stax_orchestrator_mock = mocker.patch("functions.get_task_status.app.StaxOrchestrator")
        result: dict = {
            "task_id": "some-task-id",
            "task_info": stax_orchestrator_mock.return_value.get_task_status.return_value,
        }

        # test
        lambda_handler(event, {}) == result

        stax_orchestrator_mock.return_value.get_task_status.assert_called_once_with(event["task_id"])
