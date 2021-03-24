from user_interface.adapters.request_model_creator import RequestModelCreator
from flask import Request
from typing import List, NewType, Dict, Union
from modules.stream_verifier.infrastructure.request_models import (
    LagReportRequestModel,
    DetectionsReportRequestModel,
)
from shared.gateways.request_models import KafkaRequest, TableRequest

StreamDict = NewType("StreamDict", Dict[str, str])
DBDict = NewType("DBDict", Dict[str, str])
DetectionsRequest = NewType(
    "DetectionsRequest", Dict[str, List[Union[StreamDict, DBDict]]]
)
LagRequest = NewType("LagRequest", List[StreamDict])


class SlackRequestModelCreator(RequestModelCreator):
    def to_request_model(
        self, request: Union[LagRequest, DetectionsRequest], report: str
    ):
        if report == "lag_report":
            return self._parse_lag_request_model(request)
        if report == "detections_report":
            return self._parse_detections_request_model(request)

    def _parse_lag_request_model(self, request: LagRequest):
        request_model = LagReportRequestModel()
        for req in request:
            kafka_request = KafkaRequest(
                req["bootstrap_servers"], req["group_id"], req["topic"]
            )
            request_model.streams.append(kafka_request)

        return request_model

    def _parse_detections_request_model(self, request: DetectionsRequest):
        request_model = DetectionsReportRequestModel()
        for req in request["streams"]:
            batch_size = 1
            if "batch_size" in req:
                batch_size = req["batch_size"]
            kafka_request = KafkaRequest(
                req["bootstrap_servers"], req["group_id"], req["topic"], batch_size
            )
            request_model.streams.append(kafka_request)
        for req in request["database"]:
            table_request = TableRequest(
                req["db_url"], req["table_name"], req["table_identifiers"]
            )
            request_model.tables.append(table_request)

        return request_model
