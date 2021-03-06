import pytest
from shared.result.result import Result
from modules.stream_verifier.infrastructure.verifier import StreamVerifier
from shared.error.client_error import ClientException, ExternalException


class MockLagCalculator:
    def __init__(self, state, stream):
        self.state = state
        self.stream = stream

    def get_lag(self, parser):
        if self.state == "success":
            return Result.Ok(self.stream)
        if self.state == "check_fail":
            return Result.Ok(self.stream, check_success=False)
        if self.state == "client_error":
            return Result.Fail(ClientException("fail"))
        if self.state == "external_error":
            return Result.Fail(ExternalException("fail"))


@pytest.fixture
def success_report():
    def lag_calculator_factory(stream):
        return MockLagCalculator("success", stream)

    yield lag_calculator_factory


@pytest.fixture
def success_report():
    def lag_calculator_factory(stream):
        return MockLagCalculator("check_fail", stream)

    yield lag_calculator_factory


@pytest.fixture
def client_error_report():
    def lag_calculator_factory(stream):
        return MockLagCalculator("client_error", stream)

    yield lag_calculator_factory


@pytest.fixture
def external_error_report():
    def lag_calculator_factory(stream):
        return MockLagCalculator("external_error", stream)

    yield lag_calculator_factory


class TestLagReport:
    def test_success_with_check_success(self, success_report):
        verifier = StreamVerifier(lag_calculator_factory=success_report)
        result = verifier.get_lag_report([1, 2, 3])
        assert result.value == [1, 2, 3]

    def test_success_with_check_fail(self, success_report):
        verifier = StreamVerifier(lag_calculator_factory=success_report)
        result = verifier.get_lag_report([1, 2, 3])
        assert result.value == [1, 2, 3]
        assert not result.check_success

    def test_fail_with_client_error(self, client_error_report):
        verifier = StreamVerifier(lag_calculator_factory=client_error_report)
        result = verifier.get_lag_report([1, 2, 3])
        assert not result.success
        assert type(result.error) == ClientException

    def test_fail_with_external_error(self, external_error_report):
        verifier = StreamVerifier(lag_calculator_factory=external_error_report)
        result = verifier.get_lag_report([1, 2, 3])
        assert not result.success
        assert type(result.error) == ExternalException
