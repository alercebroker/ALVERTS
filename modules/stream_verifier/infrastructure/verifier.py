from .parsers import EntityParser
from .request_models import LagReportRequestModel
from .response_models import LagReportResponseModel
from modules.stream_verifier.domain import IStreamVerifier
from typing import List
from shared import KafkaService, Result
from modules.stream_verifier.infrastructure.parsers import ResponseModelParser
from shared.error.exceptions import ExternalException
from io import BytesIO
import fastavro


class StreamVerifier(IStreamVerifier):
    def __init__(
        self, kafka_service: KafkaService, db_service: DBService, identifiers: List[str]
    ):
        self.kafka_service = kafka_service
        self.db_service = db_service
        self._entity_parser = EntityParser()
        self._response_model_parser = ResponseModelParser()
        self._identifiers = identifiers

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

    def get_detections_report(
        self, request_model: DetectionsReportRequestModel
    ) -> Result[DetectionsReportResponseModel, Exception]:
        reports = []
        for stream, table in request_model.params():
            try:

                def process_function(kafka_response):
                    def parse_function(db_response):
                        self._entity_parser.to_detections_report(
                            db_response, kafka_response
                        )

                    values = self._process_kafka_messages(kafka_response)
                    reports.append(
                        self._check_difference(values, table, parse_function)
                    )

                self.kafka_service.consume_all(stream, process_function)
            except Exception as e:
                return Result.Fail(ExternalException("Error with kafka message: {e}"))
        combined_reports = Result.combine(reports)
        if not combined_reports.success:
            return combined_reports
        return self._response_model_parser.to_detection_report_response_model(
            combined_reports.value
        )

    def _process_kafka_messages(self, kafka_response):
        values = []
        for msg in kafka_response.data:
            bytes_msj = BytesIO(msg.value())
            reader = fastavro.reader(bytes_msj)
            data = reader.next()
            identified_data = [data[identifier] for identifier in self._identifiers]
            values.append(identified_data)

        return values

    def _check_difference(self, values: list, table: str, parser: Callable) -> list:
        if len(values) == 0:
            raise ValueError(
                "No values passed, the topic is empty or something went wrong consuming."
            )

        str_values = ",\n".join([f"('{val[0]}', {val[1]})" for val in values])
        QUERY_VALUES = self.create_base_query(table) % str_values
        return self.db_service.query(QUERY_VALUES, parser)
