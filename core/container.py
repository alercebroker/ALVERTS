from dependency_injector import containers, providers
from confluent_kafka import Consumer
from shared import KafkaService
from modules.stream_verifier.infrastructure.verifier import StreamVerifier


class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    consumer_factory = providers.Factory(Consumer)
    kafka_service = providers.Singleton(
        KafkaService, consumer_creator=consumer_factory.provider
    )
    stream_verifier = providers.Singleton(StreamVerifier, kafka_service=kafka_service)
