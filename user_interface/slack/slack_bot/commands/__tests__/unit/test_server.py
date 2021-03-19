import pytest
from unittest.mock import MagicMock
from user_interface.slack.slack_bot.commands.server import create_app
from typing import List
from shared.result.result import Result
from modules.stream_verifier.domain.lag_report import LagReport
from shared.error.exceptions import ClientException, ExternalException
from flask.helpers import url_for
from dependency_injector import providers
from shared.gateways.__tests__.kafka.mocks import MockKafkaService


@pytest.fixture
def app():
    app = create_app()
    app.container.slack_signature_verifier.override(providers.Factory(MagicMock))
    yield app
    app.container.unwire()


@pytest.fixture
def client():
    def _client(app):
        app.config["TESTING"] = True

        with app.test_client() as tclient:
            return tclient

    return _client


class TestStreamLagCheck:
    def test_should_return_success(self, client, app):
        app.container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        slack_client_mock = MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        app.container.slack_client.override(providers.Object(slack_client_mock))
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#channel",
            text="""Stream Lag Report Success\nNo group id has lag""",
        )

    def test_should_return_with_check_fail(self, client, app):
        app.container.kafka_service.override(
            providers.Factory(MockKafkaService, state="check_fail")
        )
        app.container.config.from_dict(
            {
                "streams": [
                    {"bootstrap_servers": "test", "group_id": "test", "topic": "test"}
                ]
            }
        )
        slack_client_mock = MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        app.container.slack_client.override(providers.Object(slack_client_mock))
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#channel",
            text="""Stream Lag Report Fail
Topic: test, Group Id: test, Bootstrap Servers: test, Lag: 10
""",
        )

    def test_should_return_with_client_error(self, client, app):
        app.container.kafka_service.override(
            providers.Factory(MockKafkaService, state="client_error")
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        assert response.status_code == 400
        assert response.data == b"Client Error: fail"

    def test_should_return_with_external_error(self, client, app):
        app.container.kafka_service.override(
            providers.Factory(MockKafkaService, state="external_error")
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        assert response.status_code == 500
        assert response.data == b"External Error: fail"

    def test_should_return_with_parse_error(self, client, app):
        app.container.kafka_service.override(
            providers.Factory(MockKafkaService, state="parse_error")
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        assert response.status_code == 500
        assert response.data == b"Application Error: fail"

    def test_should_return_with_request_error_with_wrong_slack_parameters(
        self, client, app
    ):
        app.container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"user_name": "user"},
        )
        assert response.status_code == 400
        assert response.data == b"Request Error: Parameters must include channel_name"

    def test_should_return_with_request_error_with_wrong_stream_parameters(
        self, client, app
    ):
        app.container.kafka_service.override(
            providers.Factory(MockKafkaService, state="client_error")
        )
        app.container.config.from_dict({"streams": [{"bootstrap_servers": "test"}]})
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        assert response.status_code == 400
        assert (
            response.data == b"Client Error: Missing 'group_id' parameter for streams"
        )
