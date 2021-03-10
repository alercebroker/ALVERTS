from shared.result.result import Result
from shared.error.exceptions import ClientException, ExternalException


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
