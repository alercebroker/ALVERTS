import pytest
from unittest.mock import MagicMock
from user_interface.slack.slack_bot.commands.server import create_app
from typing import List
from shared.gateways.request_models import StreamRequestModel
from shared.result.result import Result
from modules.stream_verifier.domain.lag_report import LagReport
from shared.error.exceptions import ClientException, ExternalException
from flask.helpers import url_for
from dependency_injector import providers
from modules.stream_verifier.infrastructure.__tests__.mocks import MockStreamVerifier


@pytest.fixture
def app():
    app = create_app()
    app.alert_system.container.config.from_dict(
        {
            "streams": [
                {"topic": "test", "group_id": "test", "bootstrap_servers": "test"}
            ]
        }
    )
    app.alert_system.container.slack_signature_verifier.override(
        providers.Factory(MagicMock)
    )
    yield app
    app.alert_system.container.unwire()


@pytest.fixture
def client():
    def _client(app):
        app.config["TESTING"] = True

        with app.test_client() as tclient:
            return tclient

    return _client


class TestStreamLagCheck:
    def test_should_return_success(self, client, app):
        app.alert_system.container.stream_verifier.override(
            providers.Factory(MockStreamVerifier, test_type="success")
        )
        slack_client_mock = MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        app.alert_system.container.slack_client.override(
            providers.Object(slack_client_mock)
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#channel",
            text="""Stream Lag Report Success:
            topic: test
            lag: 0""",
        )

    def test_should_return_with_check_fail(self, client, app):
        app.alert_system.container.stream_verifier.override(
            providers.Factory(MockStreamVerifier, test_type="check_fail")
        )
        slack_client_mock = MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        app.alert_system.container.slack_client.override(
            providers.Object(slack_client_mock)
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#channel",
            text="""Stream Lag Report Fail:
            topic: test
            lag: 10""",
        )

    def test_should_return_with_client_error(self, client, app):
        app.alert_system.container.stream_verifier.override(
            providers.Factory(MockStreamVerifier, test_type="client_error")
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        assert response.status_code == 400
        assert response.data == b"Client Error: fail"

    def test_should_return_with_external_error(self, client, app):
        app.alert_system.container.stream_verifier.override(
            providers.Factory(MockStreamVerifier, test_type="external_error")
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        assert response.status_code == 500
        assert response.data == b"External Error: fail"

    def test_should_return_with_parse_error(self, client, app):
        app.alert_system.container.stream_verifier.override(
            providers.Factory(MockStreamVerifier, test_type="parse_error")
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        assert response.status_code == 500
        assert response.data == b"Parse Error: fail"

    def test_should_return_with_request_error_with_wrong_slack_parameters(
        self, client, app
    ):
        app.alert_system.container.stream_verifier.override(
            providers.Factory(MockStreamVerifier, test_type="request_error")
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"user_name": "user"},
        )
        assert response.status_code == 400
        assert response.data == b"Request Error: Wrong slack parameters"

    def test_should_return_with_request_error_with_wrong_stream_parameters(
        self, client, app
    ):
        app.alert_system.container.stream_verifier.override(
            providers.Factory(MockStreamVerifier, test_type="request_error")
        )
        app.alert_system.container.config.from_dict(
            {"streams": [{"bootstrap_servers": "test"}]}
        )
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        assert response.status_code == 400
        assert response.data == b"Client Error: 'topic'"
