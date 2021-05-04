import pytest
from unittest import mock
from user_interface.adapters.controller import ReportController


class TestGetLagReport:
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


class TestGetDetectionsReport:
    @pytest.fixture
    def controller(self):
        return ReportController(
            mock.MagicMock(), {"detections_report": mock.MagicMock()}, mock.MagicMock()
        )

    def test_should_call_success(self, controller):
        controller.get_report(
            {
                "streams": [
                    {
                        "bootstrap_servers": "",
                        "group_id": "",
                        "topic": "",
                    }
                ],
                "database": [{"table_name": ""}],
            },
            "detections_report",
        )
        controller.request_model_creator.to_request_model.assert_called()
        controller.use_cases["detections_report"].execute.assert_called()

class TestGetStampClassificationsReport:
    @pytest.fixture
    def controller(self):
        return ReportController(
            mock.MagicMock(), {"stamp_classifications_report": mock.MagicMock()}, mock.MagicMock()
        )
    
    def test_should_call_success(self, controller):
        controller.get_report(
            {
                "database": {
                    "table_names": "",
                    "mjd_name": ""
                }
            },
            "stamp_classifications_report"
        )
        controller.request_model_creator.to_request_model.assert_called()
        controller.use_cases["stamp_classifications_report"].execute.assert_called()