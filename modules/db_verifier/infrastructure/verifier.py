import time
import fastavro
from io import BytesIO

from confluent_kafka import Consumer, KafkaError, OFFSET_BEGINNING
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError, ProgrammingError

from modules.db_verifier.domain import IsDBVerifier, DBVerifierResponse
from .utils import create_base_query
from shared import Result


class DBVerifier(IsDBVerifier):
    def __init__(
            self,
            topics: list,
            brokers: str,
            table: str,
            db_connection: str,
            group_id: str = f"db_verifier_{int(time.time())}",
            batch_size: int = 1000,
            timeout: int = 30,
            identifiers: list = ["objectId", "candid"],
            ):

        if len(identifiers) != 2:
            raise ValueError("Identifier list need to have length 2 (oid, candid).")

        self.consumer = None
        self.topics = topics
        self.batch_size = batch_size
        self.timeout = timeout
        self.identifiers = identifiers
        self.brokers = brokers

        # Creating connection
        try:
            self.engine = create_engine(db_connection)
        except ArgumentError as e:
            self.engine = None
            raise ArgumentError(f"Engine correction cannot be created ({str(e)})")

        # Creating base query
        self.QUERY = create_base_query(table)

        # Creating consumer and getting total offsets
        self.consumer = Consumer({
            "bootstrap.servers": self.brokers,
            "group.id": group_id,
            "enable.auto.commit": "false",
            "auto.offset.reset": "beginning",
            'error_cb': self.kafka_errors
        })
        self.consumer.subscribe(self.topics)
        self.total_offsets = self._get_total_offsets()
        self.end_of_topic = False

    def _get_total_offsets(self):
        """Get total offsets for the current topic.

        Returns
        -------
        int
            Total offset (messages) in topic.

        """
        self.consumer.poll()
        partitions = self.consumer.assignment()
        total_offsets = 0
        for part in partitions:
            offsets = self.consumer.get_watermark_offsets(part)
            part.offset = OFFSET_BEGINNING
            self.consumer.seek(part)
            total_offsets += offsets[1]
        return total_offsets

    def kafka_errors(self, error):
        # All Brokers Down (_ALL_BROKERS_DOWN)
        if error.code() == KafkaError._ALL_BROKERS_DOWN:
            raise ConnectionRefusedError("All Kafka Brokers are down")
        # Connection Refused
        elif error.code() == KafkaError._TRANSPORT:
            raise ConnectionRefusedError("Something went wrong trying to connect to Kafka")
        # Resolve error (_RESOLVE)
        elif error.code() == KafkaError._RESOLVE:
            raise ConnectionRefusedError(f"A broker host cannot be resolved ({self.brokers})")

    def process_message(self, message: bytes) -> list:
        bytes_msj = BytesIO(message.value())
        reader = fastavro.reader(bytes_msj)
        data = reader.next()
        return [data[identifier] for identifier in self.identifiers]

    def check_difference(self, values: list) -> list:
        if len(values) == 0:
            raise ValueError("No values passed, the topic is empty or something went wrong consuming.")

        str_values = ",\n".join([f"('{val[0]}', {val[1]})" for val in values])
        QUERY_VALUES = self.QUERY % str_values
        with self.engine.connect() as conn:
            response = conn.execute(QUERY_VALUES)
            result = response.fetchall()
        return result

    def verify(self) -> Result:
        result = []
        total_messages = 0

        # Consuming all messages from the topic
        while total_messages < self.total_offsets:
            t1 = time.time()

            t0 = time.time()
            try:
                # Getting batch
                data = self.consumer.consume(self.batch_size, timeout=self.timeout)
                print(f"Consume: {time.time() - t0}")
            except ConnectionRefusedError as e:
                return Result(success=False, check_success=False, value=None, error=e)

            # TODO: Check other possible errors.
            # Parsing avros to dict
            t0 = time.time()
            try:
                values = [self.process_message(x) for x in data]
                print(f"Parsing: {time.time() - t0}")
            except KeyError as e:
                return Result(success=False, check_success=False, value=None, error=KeyError(f"Key:{str(e)} not found in alert"))

            # Querying database to check difference
            t0 = time.time()
            try:
                difference = self.check_difference(values=values)
                print(f"Database: {time.time() - t0}")
            except ValueError as e:
                if total_messages == 0:
                    return Result(success=False, check_success=False, value=None, error=e)
            except ProgrammingError as e:
                return Result(success=False, check_success=False, value=None, error=e)

            # Saving difference
            result.extend(difference)

            # Commiting consumers
            t0 = time.time()
            self.consumer.commit(asynchronous=False)
            print(f"Commit: {time.time() - t0}")
            # Getting message count
            total_messages += len(data)
            print(f"Total: {time.time() - t1} Processed messages: {total_messages}")

            if self.end_of_topic:
                break

        response = DBVerifierResponse(result,  total_messages - len(result), len(result), total_messages)
        return Result(success=True, check_success=len(result) == 0, value=response, error=None)

    def __del__(self):
        if self.consumer:
            print("Deleting Consumer")
            self.consumer.close()
        if self.engine:
            print("Closing DB Connection")
            self.engine.dispose()
