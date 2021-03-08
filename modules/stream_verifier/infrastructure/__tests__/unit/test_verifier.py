import pytest
from modules.stream_verifier.infrastructure.verifier import StreamVerifier
from shared import ClientException, ExternalException, Result
from core import AlertSystem
from dependency_injector import providers


class MockKafkaService:
    def __init__(self, state):
        self.state = state

    def get_lag(self, request_model, parser):
        if self.state == "success":
            return Result.Ok(request_model)
        if self.state == "check_fail":
            return Result.Ok(request_model, check_success=False)
        if self.state == "client_error":
            return Result.Fail(ClientException("fail"))
        if self.state == "external_error":
            return Result.Fail(ExternalException("fail"))


@pytest.fixture
def verifier():
    app = AlertSystem()

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
