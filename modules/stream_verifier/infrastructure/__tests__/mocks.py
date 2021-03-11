from shared import ClientException, ExternalException, Result
from modules.stream_verifier.infrastructure.request_models import LagReportRequestModel
from typing import List
from modules.stream_verifier.infrastructure.response_models import (
    LagReportResponseModel,
)


class MockStreamVerifier:
    def __init__(self, test_type: str):
        self.test_type = test_type

    def get_lag_report(self, request_models: List[LagReportRequestModel]):
        if self.test_type == "success":
            report = LagReportResponseModel(
                topic="test", group_id="test", lags=[0], success=True
            )
            return Result.Ok(report)
        if self.test_type == "check_fail":
            report = LagReportResponseModel(
                topic="test", group_id="test", lags=[0, 10], success=False
            )
            return Result.Ok(report, False)
        if self.test_type == "client_error":
            return Result.Fail(ClientException("fail"))
        if self.test_type == "external_error":
            return Result.Fail(ExternalException("fail"))
        if self.test_type == "parse_error":
            return Result.Fail(Exception("fail"))
