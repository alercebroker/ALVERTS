from .parsers import StreamLagParser
from modules.stream_verifier.domain import IStreamVerifier
from .utils.utils import StreamRequestModel
from .lag_calculator import LagCalculator
from typing import Callable
from shared.result.result import Result


class StreamVerifier(IStreamVerifier):
    def __init__(self, lag_calculator_factory: Callable[..., LagCalculator]):
        self.lag_calculator_factory = lag_calculator_factory
        self._lag_parser = StreamLagParser()

    def get_lag_report(self, request_models: list):
        results = []
        for request_model in request_models:
            lag_calculator = self.lag_calculator_factory(stream=request_model)
            results.append(lag_calculator.get_lag(self._lag_parser))
        return Result.combine(results)

    def get_message_report(self, request_model: StreamRequestModel):
        print("Method not implemented yet")
