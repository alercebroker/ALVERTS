import pytest
from confluent_kafka import KafkaException, Consumer
from modules.stream_verifier.infrastructure import StreamLagParser
from shared import Result, ClientException, KafkaService
from modules.stream_verifier.domain.lag_report import LagReport
from shared.gateways.request_models import StreamRequestModel


def consumer_factory(config):
    return Consumer(config)


class TestGetLag:
    lag_parser = StreamLagParser()
    consumer = KafkaService(consumer_factory)

    def test_get_lag_zero(self, kafka_service, consume):
        consume(group_id="lag_zero", topic="test", n=5, max_messages=10)
        stream = StreamRequestModel("localhost:9094", "lag_zero", "test")
        lag = self.consumer.get_lag(stream, self.lag_parser)
        assert lag.check_success

    def test_get_lag_not_zero(self, kafka_service, consume):
        consume(group_id="lag_not_zero", topic="test", n=5, max_messages=5)
        stream = StreamRequestModel("localhost:9094", "lag_not_zero", "test")
        lag = self.consumer.get_lag(stream, self.lag_parser)
        assert lag.value.total_lag() == 5

    def test_get_lag_not_previously_consumed(self, kafka_service):
        stream = StreamRequestModel("localhost:9094", "first_consume", "test")
        lag = self.consumer.get_lag(stream, self.lag_parser)
        assert lag.value.total_lag() == 10

    def test_get_lag_topic_error(self, kafka_service):
        stream = StreamRequestModel("localhost:9094", "anything", ["non_existent"])
        with pytest.raises(KafkaException):
            lag = self.consumer.get_lag(stream, self.lag_parser)
