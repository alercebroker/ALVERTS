import pytest
from user_interface.slack.adapters.slack_presenter import SlackExporter
from unittest import mock
from modules.stream_verifier.infrastructure.response_models import (
    DetectionsReportResponseModel,
    DifferenceResponse,
    StampClassificationsReportResponseModel,
    StampDatabaseResponse
)
from datetime import datetime
import tzlocal


class TestSetSlackParameters:
    @pytest.fixture
    def exporter(self):
        return SlackExporter(mock.MagicMock(), mock.MagicMock(), view={})

    def test_should_handle_error(self, exporter):
        exporter.set_slack_parameters({})
        assert exporter.view["status_code"] == 400
        assert (
            exporter.view["data"]
            == "Request Error: Parameters must include channel_names"
        )

    def test_should_set_parameters(self, exporter):
        exporter.set_slack_parameters({"channel_names": "test"})
        assert exporter.slack_parameters.get("channel_names") == "test"


class TestExportLagReport:
    @pytest.fixture
    def exporter(self):
        return SlackExporter(mock.MagicMock(), mock.MagicMock(), view={})

    def test_should_handle_error_with_params_not_set(self, exporter):
        exporter.export_lag_report(mock.MagicMock())
        assert exporter.view["status_code"] == 400

    def test_should_handle_error_when_parsing(self, exporter):
        exporter.set_slack_parameters({"channel_names": "test"})
        report_mock = mock.MagicMock()
        report_mock.streams = ["something wrong"]
        report_mock.success = False
        exporter.export_lag_report(report_mock)
        assert exporter.view["status_code"] == 500

    def test_should_handle_error_when_posting_message(self, exporter):
        exporter.client.chat_postMessage.side_effect = Exception("test")
        exporter.set_slack_parameters({"channel_names": "test"})
        report_mock = mock.MagicMock()
        report_mock.success = True
        exporter.export_lag_report(report_mock)
        assert exporter.view["status_code"] == 500
        assert exporter.view["data"] == "External Error: Error sending message: test"

    def test_should_post_message_and_set_view_data(self, exporter):
        exporter.client.chat_postMessage.return_value.status_code = 200
        exporter.set_slack_parameters({"channel_names": "test"})
        exporter.export_lag_report(mock.MagicMock())
        assert exporter.view["status_code"] == 200


class TestExportDetectionsReport:
    @pytest.fixture
    def exporter(self):
        return SlackExporter(mock.MagicMock(), mock.MagicMock(), view={})

    def test_should_handle_error_with_params_not_set(self, exporter):
        exporter.export_detections_report(mock.MagicMock())
        assert exporter.view["status_code"] == 400

    def test_should_handle_error_when_parsing(self, exporter):
        exporter.set_slack_parameters({"channel_names": "test"})
        report_mock = mock.MagicMock()
        report_mock.streams = ["something wrong"]
        report_mock.success = False
        exporter.export_detections_report(report_mock)
        assert exporter.view["status_code"] == 500

    def test_should_handle_error_when_posting_message(self, exporter):
        exporter.client.chat_postMessage.side_effect = Exception("test")
        exporter.set_slack_parameters({"channel_names": "test"})
        report_mock = mock.MagicMock()
        report_mock.success = True
        exporter.export_detections_report(report_mock)
        assert exporter.view["status_code"] == 500
        assert exporter.view["data"] == "External Error: Error sending message: test"

    def test_should_post_message_and_set_view_data(self, exporter):
        exporter.client.chat_postMessage.return_value.status_code = 200
        exporter.set_slack_parameters({"channel_names": "test"})
        exporter.export_detections_report(mock.MagicMock())
        assert exporter.view["status_code"] == 200

class TestExportStampClassificationsReport:
    @pytest.fixture
    def exporter(self):
        return SlackExporter(mock.MagicMock(), mock.MagicMock(), view={})
    
    def test_should_handle_error_with_params_not_set(self, exporter):
        exporter.export_stamp_classifications_report(mock.MagicMock())
        assert exporter.view["status_code"] == 400
    
    def test_should_handle_error_when_parsing(self, exporter):
        exporter.set_slack_parameters({"channel_names": "test"})
        report_mock = mock.MagicMock()
        report_mock.databases = ["something wrong"]
        exporter.export_stamp_classifications_report(report_mock)
        assert exporter.view["status_code"] == 500

    def test_should_handle_error_when_posting_message(self, exporter):
        exporter.client.chat_postMessage.side_effect = Exception("test")
        exporter.set_slack_parameters({"channel_names": "test"})
        report_mock = mock.MagicMock()
        report_mock.success = True
        exporter.export_stamp_classifications_report(report_mock)
        assert exporter.view["status_code"] == 500
        assert exporter.view["data"] == "External Error: Error sending message: test"
    
    def test_should_post_message_and_set_view_data(self, exporter):
        exporter.client.chat_postMessage.return_value.status_code = 200
        exporter.set_slack_parameters({"channel_names": "test"})
        exporter.export_stamp_classifications_report(mock.MagicMock())
        assert exporter.view["status_code"] == 200

class TestParseDetectionsToString:
    @pytest.fixture
    def exporter(self):
        return SlackExporter(mock.MagicMock(), mock.MagicMock(), view={})

    def test_should_return_correct_text_fail(self, exporter):
        difference = DifferenceResponse("test", "test", "test", [1, 2, 3], 3, 0)
        report = DetectionsReportResponseModel(streams=[difference], success=False)
        text = exporter._parse_detections_report_to_string(report)
        assert (
            text
            == """Detections Report Failed
Topic test from test with group id test processed 0 out of 3 alerts with 3 missing\n"""
        )

    def test_should_return_correct_text_success(self, exporter):
        difference = DifferenceResponse("test", "test", "test", [], 3, 3)
        report = DetectionsReportResponseModel(streams=[difference], success=True)
        text = exporter._parse_detections_report_to_string(report)
        assert (
            text
            == """Detections Report Success
Topic test from test with group id test processed 3 out of 3 alerts with 0 missing\n"""
        )

class TestParseStampClassificationsToString:
    @pytest.fixture
    def exporter(self):
        return SlackExporter(mock.MagicMock(), mock.MagicMock(), view={})
    
    def test_should_return_correct_text_with_no_alerts(self, exporter):
        database = StampDatabaseResponse([], 0, 0, "test", "test") 
        tz = tzlocal.get_localzone()
        today = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %z")
        report = StampClassificationsReportResponseModel(databases = [database], success= True)
        text = exporter._parse_stamp_classifications_report_to_string(report)
        assert (
            text
            == f""":astronaut: :page_facing_up: ALeRCE's report of today ({today}):\n\t• Database: test\n\t• Host: test\n\t:red_circle: No alerts today\n\t"""
        )
    
    def test_should_return_correct_text_success(self, exporter):
        counts = [('class1', 10), ('class2', 20), ('class3', 30)]
        database = StampDatabaseResponse(counts, 1, 1, "test", "test") 
        res = ""
        for r in counts:
            res += f"\t\t\t - {r[0]:<8}: {r[1]:>7}\n"
        tz = tzlocal.get_localzone()
        today = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %z")
        report = StampClassificationsReportResponseModel(databases = [database], success= True) 
        text = exporter._parse_stamp_classifications_report_to_string(report)
        assert (
            text
            == f""":astronaut: :page_facing_up: ALeRCE's report of today ({today}):\n\t• Database: test\n\t• Host: test\n\t• Objects observed last night: {database.observed:>7} :night_with_stars:\n\t• New objects observed last night: {database.new_objects:>7} :full_moon_with_face:\n\t• Stamp classifier distribution: \n {res}\t"""
        )