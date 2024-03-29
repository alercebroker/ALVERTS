import pytest
from shared import ClientException, ExternalException
from shared.gateways.__tests__.kafka.mocks import MockKafkaService
from shared.gateways.__tests__.psql.mocks import MockPsqlService
from modules.stream_verifier.infrastructure import (
    StreamVerifier,
    EntityParser,
    ResponseModelParser,
)
from modules.stream_verifier.infrastructure.request_models import (
    DetectionsReportRequestModel,
    StampClassificationsReportRequestModel,
    StampClassificationsDBRequest,
    DetectionsTableRequest,
    LagReportRequestModel,
    DetectionsTableRequest,
    DetectionsStreamRequest,
)
from shared.gateways.request_models import KafkaRequest


@pytest.fixture
def verifier():
    def _create(test_case_kafka: str, report_type: str, test_case_psql: str = None):
        if not test_case_psql:
            test_case_psql = test_case_kafka
        verifier = StreamVerifier(
            MockKafkaService(test_case_kafka),
            MockPsqlService(test_case_psql, report_type),
        )
        return verifier

    return _create


class TestLagReport:
    def test_success_with_check_success(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        result = verifier("success", "lag_report").get_lag_report(
            LagReportRequestModel(streams)
        )
        assert result.success
        assert result.value.success

    def test_success_with_check_fail(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        result = verifier("check_fail", "lag_report").get_lag_report(
            LagReportRequestModel(streams)
        )
        assert result.success
        assert not result.value.success

    def test_fail_with_client_error(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        result = verifier("client_error", "lag_report").get_lag_report(
            LagReportRequestModel(streams)
        )
        assert not result.success
        assert type(result.error) == ClientException

    def test_fail_with_external_error(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        result = verifier("external_error", "lag_report").get_lag_report(
            LagReportRequestModel(streams)
        )
        assert not result.success
        assert type(result.error) == ExternalException


class TestDetectionsReport:
    def test_success_with_check_success(self, verifier):
        streams = [
            DetectionsStreamRequest(
                "test", "test", "test", batch_size=1, identifiers=["oid", "candid"]
            )
        ]
        tables = [DetectionsTableRequest("test", "test", "test")]
        result = verifier("success", "detections_report").get_detections_report(
            DetectionsReportRequestModel(streams, tables)
        )
        assert result.success
        assert result.value.success

    def test_success_with_check_fail(self, verifier):
        streams = [
            DetectionsStreamRequest(
                "test", "test", "test", batch_size=1, identifiers=["oid", "candid"]
            )
        ]
        tables = [DetectionsTableRequest("test", "test", "test")]
        result = verifier("check_fail", "detections_report").get_detections_report(
            DetectionsReportRequestModel(streams, tables)
        )
        assert result.success
        assert not result.value.success
        assert len(result.value.streams) == 1
        for stream in result.value.streams:
            assert stream.processed == 0
            assert len(stream.difference) == 2

    def test_fail_with_kafka_error(self, verifier):
        streams = [
            DetectionsStreamRequest(
                "test", "test", "test", batch_size=1, identifiers=["oid", "candid"]
            )
        ]
        tables = [DetectionsTableRequest("test", "test", "test")]
        result = verifier(
            "external_error", "detections_report", "success"
        ).get_detections_report(DetectionsReportRequestModel(streams, tables))
        assert not result.success
        assert type(result.error) == ExternalException

    def test_fail_with_psql_error(self, verifier):
        streams = [
            DetectionsStreamRequest(
                "test", "test", "test", batch_size=1, identifiers=["oid", "candid"]
            )
        ]
        tables = [DetectionsTableRequest("test", "test", "test")]
        result = verifier(
            "success", "detections_report", "external_error"
        ).get_detections_report(DetectionsReportRequestModel(streams, tables))
        assert not result.success
        assert type(result.error) == ExternalException


class TestStampClassificationsReport:
    def test_success_with_check_success(self, verifier):
        databases = [StampClassificationsDBRequest("test", ["test1", "test2"], "test")]
        result = verifier(
            "success", "stamp_classifications_report"
        ).get_stamp_classifications_report(
            StampClassificationsReportRequestModel(databases)
        )
        assert result.success
        assert result.value.success

    def test_success_with_check_fail(self, verifier):
        databases = [StampClassificationsDBRequest("test", ["test1", "test2"], "test")]
        result = verifier(
            "check_fail", "stamp_classifications_report"
        ).get_stamp_classifications_report(
            StampClassificationsReportRequestModel(databases)
        )
        assert result.success
        assert result.value.success

    def test_fail_with_psql_error(self, verifier):
        databases = [StampClassificationsDBRequest("test", "test", "test")]
        result = verifier(
            "external_error", "stamp_classifications_report"
        ).get_stamp_classifications_report(
            StampClassificationsReportRequestModel(databases)
        )
        assert not result.success
        assert type(result.error) == ExternalException
