from shared.result.result import Result
from shared.error.exceptions import ClientException, ExternalException
from modules.stream_verifier.domain.lag_report import LagReport
from unittest import mock
from shared.gateways.response_models import KafkaResponse
from fastavro import writer, parse_schema
import io


schema = {
    "doc": "test",
    "name": "Test",
    "namespace": "test",
    "type": "record",
    "fields": [
        {"name": "oid", "type": "string"},
        {"name": "candid", "type": "long"},
    ],
}
parsed_schema = parse_schema(schema)

# 'records' can be an iterable (including generator)
records = [
    {u"oid": u"oid1", u"candid": 123},
    {u"oid": u"oid2", u"candid": 456},
]


class MockKafkaService:
    def __init__(self, state):
        self.state = state

    def get_lag(self, request_model, parser):
        if self.state == "success":
            lag_report = LagReport(
                bootstrap_servers=request_model.bootstrap_servers,
                topic=request_model.topic,
                group_id=request_model.group_id,
                lags=[0, 0, 0],
            )
            return Result.Ok(lag_report)
        if self.state == "check_fail":
            lag_report = LagReport(
                bootstrap_servers=request_model.bootstrap_servers,
                topic=request_model.topic,
                group_id=request_model.group_id,
                lags=[0, 6, 4],
            )
            return Result.Ok(lag_report)
        if self.state == "client_error":
            return Result.Fail(ClientException("fail"))
        if self.state == "external_error":
            return Result.Fail(ExternalException("fail"))
        if self.state == "parse_error":
            return Result.Fail(Exception("fail"))

    def consume_all(self, request, process):
        if self.state == "success":
            msg1 = mock.MagicMock()
            msg2 = mock.MagicMock()
            avro = io.BytesIO()
            writer(avro, parsed_schema, [records[0]])
            msg1.value.return_value = avro
            avro = io.BytesIO()
            writer(avro, parsed_schema, [records[1]])
            msg2.value.return_value = avro
            response = KafkaResponse(
                bootstrap_servers=request.bootstrap_servers,
                topic=request.topic,
                group_id=request.group_id,
                data=[msg1, msg2],
            )
            process(response)
