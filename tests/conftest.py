from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
import psycopg2
import os
import pytest
import glob
from fastavro import reader
from db_plugins.db.sql import SQLConnection
from db_plugins.db.sql.models import Detection, Object, Probability

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_PATH = os.path.abspath(os.path.join(FILE_PATH, "./examples"))


@pytest.fixture(scope="session")
def docker_compose_command():
    print("ENTRA")
    return "docker-compose" if os.getenv("COMPOSE", "v2") == "v1" else "docker compose"


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(
        str(pytestconfig.rootdir),
        "tests",
        "docker-compose.yml",
    )


def read_avro():
    files = glob.glob(os.path.join(EXAMPLES_PATH, "*.avro"))
    files.sort()
    nfiles = len(files)
    for f in files:
        with open(f, "rb") as fo:
            yield fo.read()


def is_responsive_kafka(url):
    client = AdminClient({"bootstrap.servers": url})
    topics = ["test", "test2"]
    new_topics = [NewTopic(topic, num_partitions=1) for topic in topics]
    fs = client.create_topics(new_topics)
    for topic, f in fs.items():
        try:
            f.result()
            return True
        except Exception as e:
            return False


@pytest.fixture(scope="session")
def kafka_service(docker_ip, docker_services):
    """Ensure that Kafka service is up and responsive."""
    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("kafka", 9094)
    server = "{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=60.0, pause=0.1, check=lambda: is_responsive_kafka(server)
    )

    return server


@pytest.fixture
def produce_fake_messages():
    msgs = []
    topics = ["test"]
    for i in range(10):
        msgs.append(f"test{i}")
    config = {"bootstrap.servers": "localhost:9094"}
    producer = Producer(config)
    try:
        for topic in topics:
            for data in msgs:
                producer.produce(topic, value=data)
                producer.flush(30)
            print(f"produced to {topic}")
    except Exception as e:
        print(f"failed to produce to topic {topic}: {e}")
    yield "produced"
    a = AdminClient(config)
    fs = a.delete_topics(topics, operation_timeout=30)
    # Wait for operation to finish.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} deleted".format(topic))
        except Exception as e:
            print("Failed to delete topic {}: {}".format(topic, e))


@pytest.fixture
def produce_from_avro():
    topics = ["test", "test2"]
    config = {"bootstrap.servers": "localhost:9094"}
    producer = Producer(config)
    try:
        for topic in topics:
            for data in read_avro():
                producer.produce(topic, value=data)
                producer.flush()
            print(f"produced to {topic}")
    except Exception as e:
        print(f"failed to produce to topic {topic}: {e}")
    yield "produced"
    a = AdminClient(config)
    fs = a.delete_topics(topics, operation_timeout=30)
    # Wait for operation to finish.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} deleted".format(topic))
        except Exception as e:
            print("Failed to delete topic {}: {}".format(topic, e))


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


def is_responsive_psql(url):
    try:
        conn = psycopg2.connect(
            f"dbname='postgres' user='postgres' host=localhost password='postgres'"
        )
        conn.close()
        return True
    except:
        return False


@pytest.fixture(scope="session")
def psql_service(docker_ip, docker_services):
    """Ensure that psql service is up and responsive."""
    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("postgres", 5432)
    server = "{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive_psql(server)
    )

    return server


@pytest.fixture(scope="session")
def second_database(docker_ip, docker_services):
    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("postgres_second", 5432)
    server = "{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive_psql(server)
    )
    return server


def init_db(insert: bool, config: dict):
    db = SQLConnection()
    db.connect(config)
    db.create_db()
    if insert:
        obj = Object(oid="ZTF19aaapkto", firstmjd=100000000, lastmjd=100000000)
        db.session.add(obj)
        det = Detection(
            candid=1000151433015015013,
            oid="ZTF19aaapkto",
            mjd=123,
            fid=1,
            pid=0.5,
            isdiffpos=1,
            ra=0.5,
            dec=0.5,
            magpsf=0.5,
            sigmapsf=0.5,
            corrected=False,
            dubious=False,
            has_stamp=False,
            step_id_corr="test",
        )
        db.session.add(det)
        prob = Probability(
            oid="ZTF19aaapkto",
            ranking=1,
            class_name="class_1",
            classifier_name="stamp_classifier",
            probability=0.5,
            classifier_version="classifier_version_1",
        )
        db.session.add(prob)
        db.session.commit()


def remove_db(config: dict):
    db = SQLConnection()
    db.connect(config)
    db.drop_db()


@pytest.fixture
def init_first_db():
    config = {
        "SQL": {
            "ENGINE": "postgresql",
            "HOST": "localhost",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "PORT": 5432,  # postgresql tipically runs on port 5432. Notice that we use an int here.
            "DB_NAME": "postgres",
        },
        "SQLALCHEMY_DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/postgres",
    }

    def _init(insert: bool):
        init_db(insert, config)

    yield _init

    remove_db(config)


@pytest.fixture
def init_second_db():
    config = {
        "SQL": {
            "ENGINE": "postgresql",
            "HOST": "localhost",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "PORT": 5433,  # postgresql tipically runs on port 5432. Notice that we use an int here.
            "DB_NAME": "postgres",
        },
        "SQLALCHEMY_DATABASE_URL": "postgresql://postgres:postgres@localhost:5433/postgres",
    }

    def _init(insert: bool):
        init_db(insert, config)

    yield _init

    remove_db(config)
