from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
import os
import pytest


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(
        str(pytestconfig.rootdir),
        "shared/gateways/__tests__/kafka/integration",
        "docker-compose.yml",
    )


def is_responsive_kafka(url):
    client = AdminClient({"bootstrap.servers": url})
    topics = ["test"]
    new_topics = [NewTopic(topic, num_partitions=1) for topic in topics]
    fs = client.create_topics(new_topics)
    for topic, f in fs.items():
        try:
            f.result()
            return True
        except Exception as e:
            return False


def generateMessages(n):
    msgs = []
    for i in range(n):
        msgs.append(f"test{i}")
    return msgs


@pytest.fixture(scope="session")
def kafka_service(docker_ip, docker_services):
    """Ensure that Kafka service is up and responsive."""
    topics = ["test"]
    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("kafka", 9094)
    server = "{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive_kafka(server)
    )
    config = {"bootstrap.servers": "localhost:9094"}
    producer = Producer(config)
    messages = generateMessages(10)
    try:
        for topic in topics:
            for data in messages:
                producer.produce(topic, value=data)
                producer.flush(30)
            print(f"produced to {topic}")
    except Exception as e:
        print(f"failed to produce to topic {topic}: {e}")
    return server


@pytest.fixture
def consume():
    def _consume(group_id, topic, n, max_messages):
        config = {
            "bootstrap.servers": "localhost:9094",
            "group.id": group_id,
            "auto.offset.reset": "beginning",
            "enable.partition.eof": "true",
            "enable.auto.commit": "false",
        }
        consumer = Consumer(config)
        consumer.subscribe(topics=[topic])
        messages = 0
        while True:
            if messages == max_messages:
                return
            msg = consumer.consume(num_messages=n, timeout=5)
            if len(msg) == 0:
                continue

            for m in msg:
                if m.error():
                    if m.error().code() == KafkaError._PARTITION_EOF:
                        return

                    elif m.error():
                        raise KafkaException(m.error())
                else:
                    messages += 1
                    if messages == max_messages:
                        break
            consumer.commit(asynchronous=False)

    return _consume
