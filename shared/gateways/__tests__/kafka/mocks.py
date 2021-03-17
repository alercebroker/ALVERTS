from shared.result.result import Result
from shared.error.exceptions import ClientException, ExternalException
from modules.stream_verifier.domain.lag_report import LagReport


class MockKafkaService:
    def __init__(self, state):
        self.state = state

    def get_lag(self, request_model, parser):
        if self.state == "success":
            lag_report = LagReport(
                bootstrap_servers=request_model.bootstrap_servers,
                topic=request_model.topic,
                group_id=request_model.group_id,
                lags=[0, 0, 0],
            )
            return Result.Ok(lag_report)
        if self.state == "check_fail":
            lag_report = LagReport(
                bootstrap_servers=request_model.bootstrap_servers,
                topic=request_model.topic,
                group_id=request_model.group_id,
                lags=[0, 6, 4],
            )
            return Result.Ok(lag_report)
        if self.state == "client_error":
            return Result.Fail(ClientException("fail"))
        if self.state == "external_error":
            return Result.Fail(ExternalException("fail"))
        if self.state == "parse_error":
            return Result.Fail(Exception("fail"))
