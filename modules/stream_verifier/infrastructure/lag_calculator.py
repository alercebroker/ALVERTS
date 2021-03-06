from confluent_kafka import KafkaError, KafkaException, Consumer
from .utils.utils import LagResponseModel, StreamRequestModel
from shared import Result, ClientException
from typing import Callable


class LagCalculator:
    def __init__(
        self,
        consumer_factory: Callable[..., Consumer],
        stream: StreamRequestModel,
    ):
        consumer_config = {
            "bootstrap.servers": stream.bootstrap_servers,
            "group.id": stream.group_id,
            "auto.offset.reset": "beginning",
            "enable.auto.commit": "false",
            "enable.partition.eof": "true",
        }
        self.consumer = consumer_factory(consumer_config)
        self.topics = [stream.topic]
        self.consume_one()

    def consume_one(self):
        self.consumer.subscribe(topics=self.topics)

        while True:
            msg = self.consumer.poll(timeout=10)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    return
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                return

    def get_lag(self, parser):
        partitions = self.consumer.assignment()
        partition_messages = self._get_messages_per_partition(partitions)
        response = LagResponseModel(self.topics[0])
        positions = self.consumer.position(partitions)
        if len(positions) == 0:
            return Result.Fail(
                ClientException(f"No offsets found for topics {self.topics}")
            )
        for pos in positions:
            if pos.offset == -1001:
                response.lags.append(0)
            else:
                response.lags.append(
                    partition_messages[f"part_{pos.partition}"] - pos.offset + 1
                )
        return parser.to_report(response)

    def _get_messages_per_partition(self, partitions):
        high_offsets = {}
        for part in partitions:
            offsets = self.consumer.get_watermark_offsets(part)
            high_offsets[f"part_{part.partition}"] = offsets[1]
        return high_offsets

    def get_messages(self, parser):
        partitions = self.consumer.assignment()
        total = 0
        for part in partitions:
            offsets = self.consumer.get_watermark_offsets(part)
            total += offsets[1]
        return parser.to_report(total)
