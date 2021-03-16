from user_interface.adapters.request_model_creator import RequestModelCreator
from flask import Request
from typing import List
from modules.stream_verifier.infrastructure.request_models import LagReportRequestModel
from shared.gateways.request_models import KafkaRequest


class SlackRequestModelCreator(RequestModelCreator):
    def to_request_model(self, request: List[dict], report: str):
        if report == "lag_report":
            return self._parse_lag_request_model(request)

    def _parse_lag_request_model(self, request: List[dict]):
        request_model = LagReportRequestModel()
        for req in request:
            kafka_request = KafkaRequest(
                req["bootstrap_servers"], req["group_id"], req["topic"]
            )
            request_model.streams.append(kafka_request)

        return request_model
