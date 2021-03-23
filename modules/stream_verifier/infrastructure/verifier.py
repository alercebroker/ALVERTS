from .parsers import EntityParser
from .request_models import LagReportRequestModel, DetectionsReportRequestModel
from .response_models import LagReportResponseModel, DetectionsReportResponseModel
from modules.stream_verifier.domain import IStreamVerifier
from typing import List, Callable
from shared import KafkaService, Result, PsqlService
from modules.stream_verifier.infrastructure.parsers import ResponseModelParser
from shared.error.exceptions import ExternalException
from io import BytesIO
import fastavro
import logging


class StreamVerifier(IStreamVerifier):
    def __init__(
        self,
        kafka_service: KafkaService,
        db_service: PsqlService,
    ):
        self.kafka_service = kafka_service
        self.db_service = db_service
        self._entity_parser = EntityParser()
        self._response_model_parser = ResponseModelParser()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

    def get_lag_report(
        self, request_model: LagReportRequestModel
    ) -> Result[LagReportResponseModel, Exception]:
        self.logger.info("Getting lag report")
        reports = []
        for stream in request_model.streams:
            reports.append(
                self.kafka_service.get_lag(stream, self._entity_parser.to_lag_report)
            )
        combined_reports = Result.combine(reports)
        if not combined_reports.success:
            self.logger.error("Failed to get lag report")
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
                        return self._entity_parser.to_detections_report(
                            db_response, kafka_response
                        )

                    self.db_service.connect(table.db_url)

                    values = self._process_kafka_messages(
                        kafka_response, table.identifiers
                    )
                    reports.append(
                        self._check_difference(values, table.table_name, parse_function)
                    )

                self.kafka_service.consume_all(stream, process_function)
            except Exception as e:
                err = f"Error with kafka message {e}"
                self.logger.error(err)
                return Result.Fail(ExternalException(err))
        combined_reports = Result.combine(reports)
        if not combined_reports.success:
            return combined_reports
        return self._response_model_parser.to_detections_report_response_model(
            combined_reports.value
        )

    def _process_kafka_messages(self, kafka_response, identifiers):
        values = []
        for msg in kafka_response.data:
            bytes_msj = BytesIO(msg.value())
            reader = fastavro.reader(bytes_msj)
            data = reader.next()
            identified_data = [data[identifier] for identifier in identifiers]
            values.append(identified_data)

        return values

    def _check_difference(self, values: list, table: str, parser: Callable) -> list:
        if len(values) == 0:
            err = "No values passed, the topic is empty or something went wrong consuming."
            self.logger.error(err)
            return Result.Fail(ValueError(err))

        str_values = ",\n".join([f"('{val[0]}', {val[1]})" for val in values])
        QUERY_VALUES = self._create_base_query(table) % str_values
        return self.db_service.execute(QUERY_VALUES, parser)

    def _create_base_query(self, table: str) -> str:
        """Create base query statement for alert ingested on DB.

        Parameters
        ----------
        table : str
            Description of parameter `table`.

        Returns
        -------
        str
            Base query statement to add values format with QUERY % VALUE_STR.

        """
        QUERY = f"""
                    WITH batch_candids (oid, candid) AS (
                        VALUES %s
                    )
                    SELECT batch_candids.oid, batch_candids.candid FROM batch_candids
                    LEFT JOIN {table} AS d ON batch_candids.candid = d.candid
                    WHERE d.candid IS NULL
                """
        return QUERY
