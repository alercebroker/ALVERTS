from user_interface.adapters.request_model_creator import RequestModelCreator
from typing import Any, List, NewType, Dict, Union
from modules.stream_verifier.infrastructure.request_models import (
    LagReportRequestModel,
    DetectionsReportRequestModel,
    StampClassificationsReportRequestModel,
    StampClassificationsDBRequest,
    DetectionsTableRequest,
    DetectionsStreamRequest,
)
import datetime
from shared.gateways.request_models import KafkaRequest

DetectionsRequest = NewType("DetectionsRequest", Dict[str, List[Dict[str, Any]]])
LagRequest = NewType("LagRequest", Dict[str, List[Dict[str, str]]])
StampClassificationsRequest = NewType("StampClassificationsRequest", Dict[str, str])


class SlackRequestModelCreator(RequestModelCreator):
    def to_request_model(
        self,
        request: Union[LagRequest, DetectionsRequest, StampClassificationsRequest],
        report: str,
    ):
        if report == "lag_report":
            return self._parse_lag_request_model(request)
        if report == "detections_report":
            return self._parse_detections_request_model(request)
        if report == "stamp_classifications_report":
            return self._parse_stamp_classifications_request_model(request)

    def _parse_lag_request_model(self, request: LagRequest):
        request_model = LagReportRequestModel()
        for req in request["streams"]:
            topic = self._parse_topic(req)
            group_id = self._parse_group_id(req)
            if (
                "security_protocol" in req
                and "sasl_mechanism" in req
                and "sasl_username" in req
                and "sasl_password" in req
            ):
                kafka_request = KafkaRequest(
                    req["bootstrap_servers"],
                    group_id=group_id,
                    topic=topic,
                    security_protocol=req["security_protocol"],
                    sasl_mechanism=req["sasl_mechanism"],
                    sasl_username=req["sasl_username"],
                    sasl_password=req["sasl_password"],
                )
            else:
                kafka_request = KafkaRequest(req["bootstrap_servers"], group_id, topic)
            request_model.streams.append(kafka_request)

        return request_model

    def _parse_detections_request_model(self, request: DetectionsRequest):
        request_model = DetectionsReportRequestModel()
        for req in request["streams"]:
            batch_size = 1
            if "batch_size" in req:
                batch_size = int(req["batch_size"])
            topic = self._parse_topic(req)
            group_id = self._parse_group_id(req)
            if (
                "security_protocol" in req
                and "sasl_mechanism" in req
                and "sasl_username" in req
                and "sasl_password" in req
            ):
                kafka_request = DetectionsStreamRequest(
                    bootstrap_servers=req["bootstrap_servers"],
                    group_id=group_id,
                    topic=topic,
                    batch_size=batch_size,
                    security_protocol=req["security_protocol"],
                    sasl_mechanism=req["sasl_mechanism"],
                    sasl_username=req["sasl_username"],
                    sasl_password=req["sasl_password"],
                    identifiers=req["identifiers"],
                )
            else:
                kafka_request = DetectionsStreamRequest(
                    bootstrap_servers=req["bootstrap_servers"],
                    group_id=group_id,
                    topic=topic,
                    batch_size=batch_size,
                    identifiers=req["identifiers"],
                )

            request_model.streams.append(kafka_request)
        for req in request["database"]:
            table_request = DetectionsTableRequest(
                self._parse_db_url(req),
                req["detections_table_name"],
                req["detections_id_field"],
            )
            request_model.tables.append(table_request)

        return request_model

    def _parse_stamp_classifications_request_model(
        self, request: StampClassificationsRequest
    ):
        request_model = StampClassificationsReportRequestModel()
        for req in request["database"]:
            database_request = StampClassificationsDBRequest(
                self._parse_db_url(req), req["table_names"], req["mjd_name"]
            )
            request_model.databases.append(database_request)
        return request_model

    def _parse_topic(self, req: Union[LagRequest, DetectionsRequest]):
        if "topic" in req:
            return req["topic"]
        elif "topic_format" in req:
            date = datetime.datetime.today()
            date = date.strftime(req["date_format"])
            return req["topic_format"] % date
        else:
            raise Exception("Can't create request model")

    def _parse_group_id(self, req: Union[LagRequest, DetectionsRequest]):
        if "group_id" in req:
            return req["group_id"]
        elif "group_id_format" in req:
            yesterday = datetime.datetime.today()
            date_group_id = yesterday.strftime("%Y%m%d%H%M%S")
            return req["group_id_format"] % date_group_id
        else:
            raise Exception("Can't create request model")

    def _parse_db_url(self, req: Dict[str, str]):
        base_uri = "postgresql://{}:{}@{}:{}/{}"
        return base_uri.format(
            req["user"], req["password"], req["host"], req["port"], req["database"]
        )
