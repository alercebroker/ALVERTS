from astropy.time import Time
from datetime import datetime
from .parsers import EntityParser
from .request_models import LagReportRequestModel, DetectionsReportRequestModel, StampClassificationsReportRequestModel
from .response_models import LagReportResponseModel, DetectionsReportResponseModel, StampClassificationsReportResponseModel
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
            self.logger.error("Failed to get lag report", exc_info=True)
            return combined_reports
        response_model = self._response_model_parser.to_lag_report_response_model(
            combined_reports.value
        )
        return response_model

    def get_detections_report(
        self, request_model: DetectionsReportRequestModel
    ) -> Result[DetectionsReportResponseModel, Exception]:
        self.logger.info("Getting detections report")
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
                        kafka_response, stream.identifiers
                    )
                    reports.append(
                        self._check_difference(
                            values, table.table_name, table.id_field, parse_function
                        )
                    )

                self.kafka_service.consume_all(stream, process_function)
            except Exception as e:
                err = ExternalException(f"Error with kafka message or database {e}")
                self.logger.error(err, exc_info=True)
                return Result.Fail(err)
        combined_reports = Result.combine(reports)
        if not combined_reports.success:
            return combined_reports
        return self._response_model_parser.to_detections_report_response_model(
            combined_reports.value
        )

    def get_stamp_classifications_report(
        self, request_model: StampClassificationsReportRequestModel
    ) -> Result[StampClassificationsReportResponseModel, Exception]:
        self.logger.info("Getting stamp classifications report")
        report = None
        try:
            def parse_function(db_response):
                return self._entity_parser.to_stamp_classifications_report(
                    db_response
                )
            self.db_service.connect(request_model.db_url)
            report = self._get_stamp_classifier_inference(
                        request_model.table_names, 
                        request_model.mjd_name, 
                        parse_function
                        )
        except Exception as e:
            err = f"Error with database {e}"
            self.logger.error(err)
            return Result.Fail(ExternalException(err))
        if not report.success:
            return report
        return self._response_model_parser.to_stamp_classifications_report_response_model(
            request_model.db_url, report.value
        )

    def _get_stamp_classifier_inference(self, table_names: list, mjd_name: str, parser: Callable)-> list:
        last_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        last_mjd = int(Time(last_day).mjd)
        
        statement = f"""
                        SELECT {table_names[0]}.class_name, COUNT ({table_names[0]}.oid) FROM {table_names[0]}
                        LEFT JOIN {table_names[1]} ON {table_names[0]}.oid = {table_names[1]}.oid WHERE {table_names[0]}.ranking = 1 
                        AND {table_names[0]}.classifier_name = \'stamp_classifier\' 
                        AND {table_names[1]}.{mjd_name} >= {last_mjd}
                        GROUP BY {table_names[0]}.class_name
                    """
        
        return self.db_service.execute(statement, parser)

    def _process_kafka_messages(self, kafka_response, identifiers):
        values = []
        for msg in kafka_response.data:
            bytes_msj = BytesIO(msg.value())
            reader = fastavro.reader(bytes_msj)
            data = reader.next()
            identified_data = [data[identifier] for identifier in identifiers]
            values.append(identified_data)

        return values

    def _check_difference(
        self, values: list, table: str, id_field: str, parser: Callable
    ) -> list:
        if len(values) == 0:
            err = ValueError(
                "No values passed, the topic is empty or something went wrong consuming."
            )
            self.logger.error(err, exc_info=True)
            return Result.Fail(err)

        str_values = ",\n".join([f"('{val[0]}', {val[1]})" for val in values])
        QUERY_VALUES = self._create_base_query(table, id_field, str_values)
        return self.db_service.execute(QUERY_VALUES, parser)

    def _create_base_query(self, table: str, id_field: str, values: str) -> str:
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
                    LEFT JOIN {table} AS d ON batch_candids.candid = d.{id_field}
                    WHERE d.{id_field} IS NULL
                """
        return QUERY % values
