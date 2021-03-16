import pytest
from user_interface.slack.adapters.slack_presenter import SlackExporter
from unittest import mock


class TestSetSlackParameters:
    @pytest.fixture
    def exporter(self):
        return SlackExporter(mock.MagicMock(), mock.MagicMock(), view={})

    def test_should_handle_error(self, exporter):
        exporter.set_slack_parameters({})
        assert exporter.view["status_code"] == 400
        assert (
            exporter.view["data"]
            == "Request Error: Parameters must include channel_name"
        )

    def test_should_set_parameters(self, exporter):
        exporter.set_slack_parameters({"channel_name": "test"})
        assert exporter.slack_parameters.get("channel_name") == "test"


class TestExportLagReport:
    @pytest.fixture
    def exporter(self):
        return SlackExporter(mock.MagicMock(), mock.MagicMock(), view={})

    def test_should_handle_error_with_params_not_set(self, exporter):
        exporter.export_lag_report(mock.MagicMock())
        assert exporter.view["status_code"] == 400

    def test_should_handle_error_when_parsing(self, exporter):
        exporter.set_slack_parameters({"channel_name": "test"})
        report_mock = mock.MagicMock()
        report_mock.streams = ["something wrong"]
        report_mock.success = False
        exporter.export_lag_report(report_mock)
        assert exporter.view["status_code"] == 500

    def test_should_handle_error_when_posting_message(self, exporter):
        exporter.client.chat_postMessage.side_effect = Exception("test")
        exporter.set_slack_parameters({"channel_name": "test"})
        report_mock = mock.MagicMock()
        report_mock.success = True
        exporter.export_lag_report(report_mock)
        assert exporter.view["status_code"] == 500
        assert exporter.view["data"] == "External Error: Error sending message: test"

    def test_should_post_message_and_set_view_data(self, exporter):
        exporter.client.chat_postMessage.return_value.status_code = 200
        exporter.set_slack_parameters({"channel_name": "test"})
        exporter.export_lag_report(mock.MagicMock())
        assert exporter.view["status_code"] == 200
