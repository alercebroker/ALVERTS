import pytest
from unittest import mock
from user_interface.adapters.controller import ReportController


class TestGetReport:
    @pytest.fixture
    def controller(self):
        return ReportController(
            mock.MagicMock(), {"lag_report": mock.MagicMock()}, mock.MagicMock()
        )

    def test_should_call_success(self, controller):
        controller.get_report(
            [
                {
                    "bootstrap_servers": "",
                    "group_id": "",
                    "topic": "",
                }
            ],
            "lag_report",
        )
        controller.request_model_creator.to_request_model.assert_called()
        controller.use_cases["lag_report"].execute.assert_called()
