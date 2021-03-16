import pytest
from shared import ClientException, ExternalException
from shared.gateways.request_models import KafkaRequest
from shared.gateways.__tests__.kafka.mocks import MockKafkaService
from modules.stream_verifier.infrastructure import (
    StreamVerifier,
    EntityParser,
    ResponseModelParser,
)
from modules.stream_verifier.infrastructure.request_models import LagReportRequestModel


@pytest.fixture
def verifier():
    def _create(test_case: str):
        verifier = StreamVerifier(MockKafkaService(test_case))
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
