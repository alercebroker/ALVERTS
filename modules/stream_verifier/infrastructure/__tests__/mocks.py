from shared import ClientException, ExternalException, Result
from modules.stream_verifier.domain.lag_report import LagReport
from typing import List
from shared.gateways.request_models import StreamRequestModel


class MockStreamVerifier:
    def __init__(self, test_type: str):
        self.test_type = test_type

    def get_lag_report(self, request_models: List[StreamRequestModel]):
        if self.test_type == "success":
            report = LagReport(topic="test", lags=[0])
            return Result.Ok(report)
        if self.test_type == "check_fail":
            report = LagReport(topic="test", lags=[0, 10])
            return Result.Ok(report, False)
        if self.test_type == "client_error":
            return Result.Fail(ClientException("fail"))
        if self.test_type == "external_error":
            return Result.Fail(ExternalException("fail"))
        if self.test_type == "parse_error":
            return Result.Fail(Exception("fail"))
