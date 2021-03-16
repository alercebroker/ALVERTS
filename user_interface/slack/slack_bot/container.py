from dependency_injector import containers, providers
from confluent_kafka import Consumer
from shared.gateways.kafka import KafkaService
from modules.stream_verifier.infrastructure.verifier import StreamVerifier
from slack.web.client import WebClient
from slack.signature.verifier import SignatureVerifier
from user_interface.slack.adapters.slack_presenter import SlackExporter
from modules.stream_verifier.use_cases.get_lag_report import GetLagReport
from user_interface.adapters.controller import ReportController
from user_interface.slack.adapters.slack_request_model_creator import (
    SlackRequestModelCreator,
)


class SlackContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    # gateways
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
    slack_controller = providers.Singleton(
        ReportController,
        presenter=slack_exporter,
        use_cases=providers.Dict(
            lag_report=providers.Singleton(GetLagReport, verifier=stream_verifier),
        ),
        request_model_creator=providers.Factory(SlackRequestModelCreator),
    )
