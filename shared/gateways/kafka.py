from confluent_kafka import Consumer, KafkaError, KafkaException
from shared import Result, ClientException
from .request_models import StreamRequestModel
from .response_models import LagResponseModel


class KafkaService:
    def __init__(self, consumer_creator):
        self.consumer_creator = consumer_creator

    def create_consumer(self, stream: StreamRequestModel):
        consumer_config = {
            "bootstrap.servers": stream.bootstrap_servers,
            "group.id": stream.group_id,
            "auto.offset.reset": "beginning",
            "enable.auto.commit": "false",
            "enable.partition.eof": "true",
        }
        return self.consumer_creator(consumer_config)

    def consume_one(self, stream: StreamRequestModel, consumer=None):
        if not consumer:
            consumer = self.create_consumer(stream)
        consumer.subscribe(topics=[stream.topic])

        while True:
            msg = consumer.poll(timeout=10)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    return
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                return

    def consume(self, stream: StreamRequestModel, process):
        consumer = self.create_consumer(stream)
        topics = [stream.topic]
        consumer.subscribe(topics=topics)

        while True:
            msg = consumer.poll(timeout=10)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    return
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                process(msg)

    def get_lag(self, stream, parser):
        consumer = self.create_consumer(stream)
        self.consume_one(stream, consumer=consumer)
        partitions = consumer.assignment()
        partition_messages = self.get_messages_per_partition(partitions, consumer)
        response = LagResponseModel(stream.topic, stream.group_id)
        positions = consumer.position(partitions)
        if len(positions) == 0:
            return Result.Fail(
                ClientException(f"No offsets found for topics {self.topics}")
            )
        for i, pos in enumerate(positions):
            if pos.offset == -1001:
                response.lags.append(0)
            else:
                response.lags.append(partition_messages[i] - pos.offset + 1)
        return parser.to_report(response)

    def get_messages_per_partition(
        self, partitions=None, consumer=None, stream: StreamRequestModel = None
    ):
        if not partitions:
            consumer = self.create_consumer(stream)
            partitions = consumer.assignment()
        high_offsets = []
        for part in partitions:
            offsets = consumer.get_watermark_offsets(part)
            high_offsets.append(offsets[1])
        return high_offsets
