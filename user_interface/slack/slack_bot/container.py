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
from shared.gateways.psql import PsqlService
from modules.stream_verifier.use_cases.get_detections_report import GetDetectionsReport
from user_interface.slack.slack_bot.utils.streams import (
    get_kafka_streams_detections_report,
    get_kafka_streams_lag_report,
)


class SlackContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # gateways
    consumer_factory = providers.Factory(Consumer)
    kafka_service = providers.Singleton(
        KafkaService, consumer_creator=consumer_factory.provider
    )
    db_service = providers.Singleton(PsqlService)

    slack_client = providers.Singleton(WebClient, token=config.slack.SLACK_BOT_TOKEN)
    slack_signature_verifier = providers.Singleton(
        SignatureVerifier, signing_secret=config.slack.SLACK_SIGNATURE
    )

    # Main service
    stream_verifier = providers.Singleton(
        StreamVerifier,
        kafka_service=kafka_service,
        db_service=db_service,
    )

    # User interface
    slack_exporter = providers.Factory(
        SlackExporter,
        client=slack_client,
        signature_verifier=slack_signature_verifier,
    )
    slack_controller = providers.Factory(
        ReportController,
        presenter=slack_exporter,
        use_cases=providers.Dict(
            lag_report=providers.Factory(GetLagReport, verifier=stream_verifier),
            detections_report=providers.Factory(
                GetDetectionsReport, verifier=stream_verifier
            ),
        ),
        request_model_creator=providers.Factory(SlackRequestModelCreator),
    )

    stream_params_creator = providers.Dict(
        stream_params_lag_report=providers.Callable(get_kafka_streams_lag_report),
        stream_params_detections_report=providers.Callable(
            get_kafka_streams_detections_report
        ),
    )
