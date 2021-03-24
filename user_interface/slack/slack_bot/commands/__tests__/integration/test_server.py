import pytest
from user_interface.slack.slack_bot.commands.server import create_app
from dependency_injector import providers
from unittest.mock import MagicMock
import os
import datetime


@pytest.fixture
def app():

    app = create_app()

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
    def test_get_lag(self, kafka_service, consume, client, app):
        consume("test_get_lag_success", "test", 1, 1)
        KAFKA_STREAMS = {
            "lag_report": [
                {
                    "bootstrap_servers": "localhost:9094",
                    "topic": "test",
                    "group_id": "test_get_lag_success",
                },
            ],
        }
        app.container.config.from_dict(
            {"slack": {}, "streams": KAFKA_STREAMS, "database": {}}
        )
        slack_client_mock = MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        app.container.slack_client.override(providers.Object(slack_client_mock))
        app.container.slack_signature_verifier.override(providers.Factory(MagicMock))
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_lag_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#channel",
            text="""Stream Lag Report Success\nNo group id has lag""",
        )


class TestDetectionsCheck:
    def test_should_return_success(
        self, kafka_service, psql_service, init_first_db, client, app
    ):
        KAFKA_STREAMS = {
            "detections_report": [
                {
                    "bootstrap_servers": "localhost:9094",
                    "topic": "test",
                    "group_id": "test_detections_report_success",
                },
            ],
        }
        DATABASE_CONFIG = [
            {
                "table_identifiers": ["objectId", "candid"],
                "db_url": "postgresql://postgres:postgres@localhost:5432/postgres",
                "table_name": "detection",
            },
        ]
        app.container.config.from_dict(
            {
                "slack": {},
                "streams": KAFKA_STREAMS,
                "database": DATABASE_CONFIG,
            }
        )
        init_first_db(insert=True)
        slack_client_mock = MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        app.container.slack_client.override(providers.Object(slack_client_mock))
        app.container.slack_signature_verifier.override(providers.Factory(MagicMock))
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_detections_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#channel",
            text="""Detections Report Success
Topic test from localhost:9094 with group id test processed 1 out of 1 alerts with 0 missing
""",
        )

    def test_should_return_check_fail(
        self, kafka_service, psql_service, init_first_db, client, app
    ):
        KAFKA_STREAMS = {
            "detections_report": [
                {
                    "bootstrap_servers": "localhost:9094",
                    "topic": "test",
                    "group_id": "test_detections_report_fail",
                },
            ],
        }
        DATABASE_CONFIG = [
            {
                "table_identifiers": ["objectId", "candid"],
                "db_url": "postgresql://postgres:postgres@localhost:5432/postgres",
                "table_name": "detection",
            },
        ]
        app.container.config.from_dict(
            {
                "slack": {},
                "streams": KAFKA_STREAMS,
                "database": DATABASE_CONFIG,
            }
        )
        init_first_db(insert=False)
        slack_client_mock = MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        app.container.slack_client.override(providers.Object(slack_client_mock))
        app.container.slack_signature_verifier.override(providers.Factory(MagicMock))
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_detections_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#channel",
            text="""Detections Report Failed
Topic test from localhost:9094 with group id test processed 0 out of 1 alerts with 1 missing
""",
        )

    def test_should_return_success_with_two_databases(
        self,
        kafka_service,
        psql_service,
        second_database,
        init_first_db,
        init_second_db,
        client,
        app,
    ):
        KAFKA_STREAMS = {
            "detections_report": [
                {
                    "bootstrap_servers": "localhost:9094",
                    "topic": "test",
                    "group_id": "test_two_databases_success",
                },
                {
                    "bootstrap_servers": "localhost:9094",
                    "topic": "test2",
                    "group_id": "test2_two_databases_success",
                },
            ],
        }

        DATABASE_CONFIG = [
            {
                "table_identifiers": ["objectId", "candid"],
                "db_url": "postgresql://postgres:postgres@localhost:5432/postgres",
                "table_name": "detection",
            },
            {
                "table_identifiers": ["objectId", "candid"],
                "db_url": "postgresql://postgres:postgres@localhost:5433/postgres",
                "table_name": "detection",
            },
        ]
        app.container.config.from_dict(
            {
                "slack": {},
                "streams": KAFKA_STREAMS,
                "database": DATABASE_CONFIG,
            }
        )
        init_first_db(insert=True)
        init_second_db(insert=True)
        slack_client_mock = MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        app.container.slack_client.override(providers.Object(slack_client_mock))
        app.container.slack_signature_verifier.override(providers.Factory(MagicMock))
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_detections_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#channel",
            text="""Detections Report Success
Topic test from localhost:9094 with group id test processed 1 out of 1 alerts with 0 missing
Topic test2 from localhost:9094 with group id test2 processed 1 out of 1 alerts with 0 missing
""",
        )

    def test_should_return_check_fail_with_two_databases(
        self,
        kafka_service,
        psql_service,
        second_database,
        init_first_db,
        init_second_db,
        client,
        app,
    ):
        KAFKA_STREAMS = {
            "detections_report": [
                {
                    "bootstrap_servers": "localhost:9094",
                    "topic": "test",
                    "group_id": "test_two_databases_fail",
                },
                {
                    "bootstrap_servers": "localhost:9094",
                    "topic": "test2",
                    "group_id": "test2_two_databases_fail",
                },
            ],
        }

        DATABASE_CONFIG = [
            {
                "table_identifiers": ["objectId", "candid"],
                "db_url": "postgresql://postgres:postgres@localhost:5432/postgres",
                "table_name": "detection",
            },
            {
                "table_identifiers": ["objectId", "candid"],
                "db_url": "postgresql://postgres:postgres@localhost:5433/postgres",
                "table_name": "detection",
            },
        ]
        app.container.config.from_dict(
            {
                "slack": {},
                "streams": KAFKA_STREAMS,
                "database": DATABASE_CONFIG,
            }
        )
        init_first_db(insert=True)
        init_second_db(insert=False)
        slack_client_mock = MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        app.container.slack_client.override(providers.Object(slack_client_mock))
        app.container.slack_signature_verifier.override(providers.Factory(MagicMock))
        test_client = client(app)
        response = test_client.post(
            "/slack/stream_detections_check",
            data={"channel_name": "channel", "user_name": "user"},
        )
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#channel",
            text="""Detections Report Failed
Topic test from localhost:9094 with group id test processed 1 out of 1 alerts with 0 missing
Topic test2 from localhost:9094 with group id test2 processed 0 out of 1 alerts with 1 missing
""",
        )
