from confluent_kafka import KafkaException
import pytest
from shared import ClientException
from confluent_kafka import Consumer
from modules.stream_verifier.infrastructure import LagCalculator, StreamLagParser
from modules.stream_verifier.infrastructure.lag_calculator import (
    StreamRequestModel,
    LagResponseModel,
)
from shared.result.result import Result
from modules.stream_verifier.domain.lag_report import LagReport


def consumer_factory(config):
    return Consumer(config)


class TestGetLag:
    lag_parser = StreamLagParser()

    def test_get_lag_zero(self, kafka_service, consume):
        consume(group_id="lag_zero", topic="test", n=5, max_messages=10)
        stream = StreamRequestModel("localhost:9094", "lag_zero", "test")
        lag_calculator = LagCalculator(consumer_factory=consumer_factory, stream=stream)
        lag = lag_calculator.get_lag(self.lag_parser)
        assert lag.check_success

    def test_get_lag_not_zero(self, kafka_service, consume):
        consume(group_id="lag_not_zero", topic="test", n=5, max_messages=5)
        stream = StreamRequestModel("localhost:9094", "lag_not_zero", "test")
        lag_calculator = LagCalculator(consumer_factory=consumer_factory, stream=stream)
        lag = lag_calculator.get_lag(self.lag_parser)
        assert lag.value.total_lag() == 5

    def test_get_lag_not_previously_consumed(self, kafka_service):
        stream = StreamRequestModel("localhost:9094", "first_consume", "test")
        lag_calculator = LagCalculator(consumer_factory=consumer_factory, stream=stream)
        lag = lag_calculator.get_lag(self.lag_parser)
        assert lag.value.total_lag() == 10

    def test_get_lag_topic_error(self, kafka_service):
        stream = StreamRequestModel("localhost:9094", "anything", ["non_existent"])
        with pytest.raises(KafkaException):
            lag_calculator = LagCalculator(
                consumer_factory=consumer_factory, stream=stream
            )
            lag = lag_calculator.get_lag(self.lag_parser)
