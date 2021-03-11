from dependency_injector import containers, providers
from confluent_kafka import Consumer
from shared import KafkaService
from modules.stream_verifier.infrastructure.verifier import StreamVerifier
from user_interface.slack.adapters.slack_presenter import SlackExporter
from user_interface.slack.adapters.slack_controller import SlackController
from slack.web.client import WebClient
from slack.signature.verifier import SignatureVerifier
from modules.stream_verifier.use_cases.get_lag_report import GetLagReport


class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    consumer_factory = providers.Factory(Consumer)
    kafka_service = providers.Singleton(
        KafkaService, consumer_creator=consumer_factory.provider
    )
    stream_verifier = providers.Singleton(StreamVerifier, kafka_service=kafka_service)
    slack_client = providers.Singleton(WebClient, token=config.slack.SLACK_BOT_TOKEN)
    slack_signature_verifier = providers.Singleton(
        SignatureVerifier, signing_secret=config.slack.SLACK_SIGNATURE
    )
    slack_exporter = providers.Singleton(
        SlackExporter,
        client=slack_client,
        signature_verifier=slack_signature_verifier,
    )
    get_lag_use_case = providers.Singleton(GetLagReport, verifier=stream_verifier)
    slack_controller = providers.Singleton(
        SlackController,
        slack_exporter=slack_exporter,
        get_lag_report=get_lag_use_case,
        get_db_report=providers.Object(None),
        stream_config=config.streams,
    )
