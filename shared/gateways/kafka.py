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

    def create_consumer(self, request: KafkaRequest, custom_config={}):
        consumer_config = {
            "bootstrap.servers": request.bootstrap_servers,
            "group.id": request.group_id,
            "auto.offset.reset": "beginning",
            "enable.auto.commit": "false",
            "enable.partition.eof": "true",
            "error_cb": self.handle_error,
        }
        consumer_config.update(custom_config)
        return self.consumer_creator(consumer_config)

    def handle_error(self, error):
        if error.code() == KafkaError._PARTITION_EOF:
            return
        if error.code() == KafkaError._ALL_BROKERS_DOWN:
            raise ConnectionRefusedError("All Kafka Brokers are down")
        # Connection Refused
        # elif error.code() == KafkaError._TRANSPORT:
        #     raise ConnectionRefusedError(
        #         "Something went wrong trying to connect to Kafka"
        #     )
        # Resolve error (_RESOLVE)
        elif error.code() == KafkaError._RESOLVE:
            raise ConnectionRefusedError(
                f"A broker host cannot be resolved ({self.brokers})"
            )
        else:
            raise error

    def consume_one(self, stream: KafkaRequest, consumer=None) -> None:
        created = False
        if not consumer:
            consumer = self.create_consumer(stream)
            created = True
        consumer.subscribe(topics=[stream.topic])

        while True:
            try:
                msg = consumer.poll(timeout=10)
            except Exception as e:
                raise e
            else:
                if msg is None:
                    continue
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
            consumer = self.create_consumer(
                request,
                {
                    "enable.partition.eof": "false",
                },
            )
            created = True
        topics = [request.topic]
        try:
            self.consume_one(request, consumer=consumer)
        except Exception as e:
            return Result.Fail(ExternalException(f"Error with kafka message: {e}"))
        partitions = consumer.assignment()
        total_messages = sum(
            self.get_messages_per_partition(partitions=partitions, consumer=consumer)
        )
        consumed_messages = 0
        retries = 3
        retry_count = 0
        while total_messages > 0 and consumed_messages < total_messages:
            try:
                msgs = consumer.consume(request.batch_size, timeout=10)
            except Exception as e:
                raise e
            else:
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
        except Exception as e:
            return Result.Fail(ExternalException(f"Error with kafka message: {e}"))
        partitions = consumer.assignment()
        if len(partitions) == 0:
            return Result.Fail(
                ClientException(f"No partitions found for topics {request.topic}")
            )
        partition_messages = self.get_messages_per_partition(partitions, consumer)
        response = KafkaResponse(
            bootstrap_servers=request.bootstrap_servers,
            topic=request.topic,
            group_id=request.group_id,
            data={"lags": []},
        )
        positions = consumer.position(partitions)

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
            try:
                self.consume_one(stream, consumer=consumer)
            except Exception as e:
                raise e
            partitions = consumer.assignment()
        high_offsets = []
        for part in partitions:
            offsets = consumer.get_watermark_offsets(part)
            high_offsets.append(offsets[1])

        if created:
            consumer.close()
            del consumer
        return high_offsets
