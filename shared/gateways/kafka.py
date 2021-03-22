from confluent_kafka import Consumer, KafkaError, KafkaException
from shared import Result, ClientException
from .request_models import KafkaRequest
from .response_models import KafkaResponse
from typing import Callable, TypeVar, List
from shared.error.exceptions import ExternalException

T = TypeVar("T")
E = TypeVar("E")


class KafkaService:
    def __init__(self, consumer_creator):
        self.consumer_creator = consumer_creator

    def create_consumer(self, request: KafkaRequest):
        consumer_config = {
            "bootstrap.servers": request.bootstrap_servers,
            "group.id": request.group_id,
            "auto.offset.reset": "beginning",
            "enable.auto.commit": "false",
            "enable.partition.eof": "true",
        }
        return self.consumer_creator(consumer_config)

    def consume_one(self, stream: KafkaRequest, consumer=None) -> None:
        created = False
        if not consumer:
            consumer = self.create_consumer(stream)
            created = True
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
                break

        if created:
            consumer.close()
            del consumer

    def consume_all(
        self,
        request: KafkaRequest,
        process: Callable,
        consumer: Consumer = None,
    ):
        created = False
        if not consumer:
            consumer = self.create_consumer(request)
            created = True
        topics = [request.topic]
        try:
            self.consume_one(request, consumer=consumer)
        except KafkaException as e:
            return Result.Fail(ExternalException(f"Error with kafka message: {e}"))
        partitions = consumer.assignment()
        total_messages = sum(
            self.get_messages_per_partition(partitions=partitions, consumer=consumer)
        )
        consumed_messages = 0
        retries = 3
        retry_count = 0
        while total_messages > 0 and consumed_messages < total_messages:
            msgs = consumer.consume(request.batch_size, timeout=10)
            if len(msgs) == 0:
                if retry_count == retries:
                    # Process in case there is no messages
                    response = KafkaResponse(
                        bootstrap_servers=request.bootstrap_servers,
                        topic=request.topic,
                        group_id=request.group_id,
                        data=msgs,
                    )
                    process(response)
                    break
                retry_count += 1
                continue

            for msg in msgs:
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        pass
                    elif msg.error():
                        raise KafkaException(msg.error())
            consumed_messages += request.batch_size
            response = KafkaResponse(
                bootstrap_servers=request.bootstrap_servers,
                topic=request.topic,
                group_id=request.group_id,
                data=msgs,
            )
            process(response)
            consumer.commit()
        consumer.close()
        del consumer

    def get_lag(
        self, request: KafkaRequest, parser: Callable[..., Result[T, E]]
    ) -> Result[T, E]:
        consumer = self.create_consumer(request)
        try:
            self.consume_one(request, consumer=consumer)
        except KafkaException as e:
            return Result.Fail(ExternalException(f"Error with kafka message: {e}"))
        partitions = consumer.assignment()
        partition_messages = self.get_messages_per_partition(partitions, consumer)
        response = KafkaResponse(
            bootstrap_servers=request.bootstrap_servers,
            topic=request.topic,
            group_id=request.group_id,
            data={"lags": []},
        )
        positions = consumer.position(partitions)
        if len(positions) == 0:
            return Result.Fail(
                ClientException(f"No offsets found for topics {self.topics}")
            )
        for i, pos in enumerate(positions):
            if pos.offset == -1001:
                response.data["lags"].append(0)
            else:
                response.data["lags"].append(partition_messages[i] - pos.offset + 1)
        consumer.close()
        del consumer
        return parser(response)

    def get_messages_per_partition(
        self, partitions=None, consumer=None, stream: KafkaRequest = None
    ) -> List[int]:
        created = False
        if not partitions:
            consumer = self.create_consumer(stream)
            created = True
            self.consume_one(stream, consumer=consumer)
            partitions = consumer.assignment()
        high_offsets = []
        for part in partitions:
            offsets = consumer.get_watermark_offsets(part)
            high_offsets.append(offsets[1])

        if created:
            consumer.close()
            del consumer
        return high_offsets
