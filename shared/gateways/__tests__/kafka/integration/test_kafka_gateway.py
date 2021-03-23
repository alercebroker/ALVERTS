import pytest
from confluent_kafka import KafkaException, Consumer
from modules.stream_verifier.infrastructure.parsers import EntityParser
from shared import Result, ClientException, KafkaService
from modules.stream_verifier.domain.lag_report import LagReport
from shared.gateways.request_models import KafkaRequest
from unittest import mock


def consumer_factory(config):
    return Consumer(config)


class TestGetLag:
    parser = EntityParser()
    consumer = KafkaService(consumer_factory)

    def test_get_lag_zero(self, kafka_service, consume):
        consume(group_id="lag_zero", topic="test", n=5, max_messages=10)
        stream = KafkaRequest("localhost:9094", "lag_zero", "test")
        lag = self.consumer.get_lag(stream, self.parser.to_lag_report)
        assert lag.success
        assert lag.value.check_success()

    def test_get_lag_not_zero(self, kafka_service, consume):
        consume(group_id="lag_not_zero", topic="test", n=5, max_messages=5)
        stream = KafkaRequest("localhost:9094", "lag_not_zero", "test")
        lag = self.consumer.get_lag(stream, self.parser.to_lag_report)
        assert lag.success
        assert lag.value.total_lag() == 5
        assert not lag.value.check_success()

    def test_get_lag_not_previously_consumed(self, kafka_service):
        stream = KafkaRequest("localhost:9094", "first_consume", "test")
        lag = self.consumer.get_lag(stream, self.parser.to_lag_report)
        assert lag.success
        assert lag.value.total_lag() == 10
        assert not lag.value.check_success()

    def test_get_lag_topic_error(self, kafka_service):
        stream = KafkaRequest("localhost:9094", "anything", "non_existent")
        lag = self.consumer.get_lag(stream, self.parser.to_lag_report)
        assert not lag.success
        assert "No partitions found for topics non_existent" in str(lag.error)


class TestConsumeAll:
    parser = EntityParser()
    consumer = KafkaService(consumer_factory)

    def test_consume_all(self, kafka_service):
        stream = KafkaRequest("localhost:9094", "test_consume_all", "test", 1)
        process = mock.MagicMock()
        self.consumer.consume_all(stream, process)
        assert process.call_count == 10

    def test_consume_all_topic_error(self, kafka_service):
        stream = KafkaRequest("localhost:9094", "anything", "non_existent")
        with pytest.raises(ClientException) as e:
            lag = self.consumer.consume_all(stream, mock.MagicMock())
            assert "No partitions found for topics non_existent" in str(e)
