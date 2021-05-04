import pytest
from shared import ClientException, ExternalException
from shared.gateways.request_models import KafkaRequest, TableRequest
from shared.gateways.__tests__.kafka.mocks import MockKafkaService
from shared.gateways.__tests__.psql.mocks import MockPsqlService
from modules.stream_verifier.infrastructure import (
    StreamVerifier,
    EntityParser,
    ResponseModelParser,
)
from modules.stream_verifier.infrastructure.request_models import (
    LagReportRequestModel,
    DetectionsReportRequestModel,
    StampClassificationsReportRequestModel
)


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
        result = verifier("success").get_lag_report(LagReportRequestModel(streams))
        assert result.success
        assert result.value.success

    def test_success_with_check_fail(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        result = verifier("check_fail").get_lag_report(LagReportRequestModel(streams))
        assert result.success
        assert not result.value.success

    def test_fail_with_client_error(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        result = verifier("client_error").get_lag_report(LagReportRequestModel(streams))
        assert not result.success
        assert type(result.error) == ClientException

    def test_fail_with_external_error(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        result = verifier("external_error").get_lag_report(
            LagReportRequestModel(streams)
        )
        assert not result.success
        assert type(result.error) == ExternalException


class TestDetectionsReport:
    def test_success_with_check_success(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        tables = [TableRequest("test", "test", ["oid", "candid"])]
        result = verifier("success").get_detections_report(
            DetectionsReportRequestModel(streams, tables)
        )
        assert result.success
        assert result.value.success

    def test_success_with_check_fail(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        tables = [TableRequest("test", "test", ["oid", "candid"])]
        result = verifier("check_fail").get_detections_report(
            DetectionsReportRequestModel(streams, tables)
        )
        assert result.success
        assert not result.value.success
        assert len(result.value.streams) == 1
        for stream in result.value.streams:
            assert stream.processed == 0
            assert len(stream.difference) == 2

    def test_fail_with_kafka_error(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        tables = [TableRequest("test", "test", ["oid", "candid"])]
        result = verifier("external_error", "success").get_detections_report(
            DetectionsReportRequestModel(streams, tables)
        )
        assert not result.success
        assert type(result.error) == ExternalException

    def test_fail_with_psql_error(self, verifier):
        streams = [KafkaRequest("test", "test", "test")]
        tables = [TableRequest("test", "test", ["oid", "candid"])]
        result = verifier("success", "external_error").get_detections_report(
            DetectionsReportRequestModel(streams, tables)
        )
        assert not result.success
        assert type(result.error) == ExternalException

class TestStampClassificationsReport:
    def test_success_with_check_success(self, verifier):
        db_url = "test"
        table_names = ["test1", "test2"]
        mjd_name = "test"
        result = verifier("success", "stamp_classifications_report").get_stamp_classifications_report(
            StampClassificationsReportRequestModel(db_url, table_names, mjd_name)
        )
        assert result.success
        assert result.value.success
    def test_fail_with_psql_error(self, verifier):
        db_url = "test"
        table_names = ["test1", "test2"]
        mjd_name = "test"
        result = verifier("external_error", "stamp_classifications_report").get_stamp_classifications_report(
            StampClassificationsReportRequestModel(db_url, table_names, mjd_name)
        )
        assert not result.success
        assert type(result.error) == ExternalException