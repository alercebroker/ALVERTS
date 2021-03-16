from .parsers import EntityParser
from .request_models import LagReportRequestModel
from .response_models import LagReportResponseModel
from modules.stream_verifier.domain import IStreamVerifier
from typing import List
from shared import KafkaService, Result
from modules.stream_verifier.infrastructure.parsers import ResponseModelParser


class StreamVerifier(IStreamVerifier):
    def __init__(self, kafka_service: KafkaService):
        self.kafka_service = kafka_service
        self._entity_parser = EntityParser()
        self._response_model_parser = ResponseModelParser()

    def get_lag_report(
        self, request_model: LagReportRequestModel
    ) -> Result[LagReportResponseModel, Exception]:
        reports = []
        for stream in request_model.streams:
            reports.append(
                self.kafka_service.get_lag(stream, self._entity_parser.to_lag_report)
            )
        combined_reports = Result.combine(reports)
        if not combined_reports.success:
            return combined_reports
        response_model = self._response_model_parser.to_lag_report_response_model(
            combined_reports.value
        )
        return response_model
