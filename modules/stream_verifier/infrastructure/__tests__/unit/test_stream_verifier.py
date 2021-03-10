import pytest
from shared import ClientException, ExternalException
from shared.gateways.__tests__.kafka.mocks import MockKafkaService
from core import AlertSystem
from dependency_injector import providers


@pytest.fixture
def verifier():
    app = AlertSystem({})

    def _verifier(state):
        factory = providers.Factory(MockKafkaService, state=state)
        app.container.kafka_service.override(factory)
        return app.container.stream_verifier()

    yield _verifier
    app.container.unwire()


class TestLagReport:
    def test_success_with_check_success(self, verifier):
        result = verifier("success").get_lag_report([1, 2, 3])
        assert result.value == [1, 2, 3]

    def test_success_with_check_fail(self, verifier):
        result = verifier("check_fail").get_lag_report([1, 2, 3])
        assert result.value == [1, 2, 3]
        assert not result.check_success

    def test_fail_with_client_error(self, verifier):
        result = verifier("client_error").get_lag_report([1, 2, 3])
        assert not result.success
        assert type(result.error) == ClientException

    def test_fail_with_external_error(self, verifier):
        result = verifier("external_error").get_lag_report([1, 2, 3])
        assert not result.success
        assert type(result.error) == ExternalException
