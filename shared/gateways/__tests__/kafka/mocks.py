from shared.result.result import Result
from shared.error.exceptions import ClientException, ExternalException
from modules.stream_verifier.infrastructure.response_models import (
    LagReportResponseModel,
)


class MockKafkaService:
    def __init__(self, state):
        self.state = state

    def get_lag(self, request_model, parser):
        if self.state == "success":
            lag_report = LagReportResponseModel(
                topic="test", group_id="test", lags=[0], success=True
            )
            return Result.Ok(lag_report)
        if self.state == "check_fail":
            lag_report = LagReportResponseModel(
                topic="test", group_id="test", lags=[0, 10], success=False
            )
            return Result.Ok(lag_report, check_success=False)
        if self.state == "client_error":
            return Result.Fail(ClientException("fail"))
        if self.state == "external_error":
            return Result.Fail(ExternalException("fail"))
