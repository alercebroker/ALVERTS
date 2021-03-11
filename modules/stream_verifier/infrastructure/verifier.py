from .parsers import StreamLagParser
from .request_models import LagReportRequestModel
from modules.stream_verifier.domain import IStreamVerifier
from typing import List
from shared import KafkaService, Result


class StreamVerifier(IStreamVerifier):
    def __init__(self, kafka_service: KafkaService):
        self.kafka_service = kafka_service
        self._lag_parser = StreamLagParser()

    def get_lag_report(self, request_models: List[LagReportRequestModel]):
        results = []
        for request_model in request_models:
            results.append(self.kafka_service.get_lag(request_model, self._lag_parser))
        return Result.combine(results)

    def get_message_report(self, request_model):
        print("Method not implemented yet")
