import pytest
from unittest import mock
from user_interface.slack.slack_bot.schedule import bot
from user_interface.slack.slack_bot.container import SlackContainer
from typing import List, NewType, Tuple
from dependency_injector import providers
import sys
import datetime

BOT_FIXTURE = NewType("BOT_FIXTURE", Tuple[bot.ScheduledBot, SlackContainer])


@pytest.fixture
def bot_fixture():
    container = SlackContainer()
    container.config.from_yaml(
        "user_interface/slack/slack_bot/schedule/__tests__/settings.yml"
    )
    container.wire(modules=[sys.modules[bot.__name__]])
    container.slack_signature_verifier.override(providers.Factory(mock.MagicMock))
    scheduled_bot: bot.ScheduledBot = bot.ScheduledBot()
    yield scheduled_bot, container
    container.unwire()


class TestStreamLagCheck:
    def test_should_return_success_report_and_post_to_slack(
        self, kafka_service, consume, bot_fixture
    ):
        consume("test_get_lag_success", "test", 1, 1)

        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]

        local_settings = {
            "slack_bot": {
                "reports": [
                    {
                        "name": "lag_report",
                        "streams": [
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test",
                                "group_id": "test_get_lag_success",
                            }
                        ],
                    }
                ]
            }
        }
        container.config.from_dict(local_settings)

        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        container.slack_signature_verifier.override(providers.Factory(mock.MagicMock))
        response = scheduled_bot.lag_report()
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#test-bots",
            text="""Stream Lag Report Success\nNo group id has lag""",
        )
        assert response["status_code"] == 200

    def test_should_return_success_report_and_fail_post_to_slack(
        self, kafka_service, consume, bot_fixture: BOT_FIXTURE
    ):
        consume("test_get_lag_success_slack_error", "test", 1, 1)
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]

        local_settings = {
            "slack_bot": {
                "reports": [
                    {
                        "name": "lag_report",
                        "streams": [
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test",
                                "group_id": "test_get_lag_success_slack_error",
                            }
                        ],
                    }
                ]
            }
        }
        container.config.from_dict(local_settings)

        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.side_effect = Exception(
            "Failed to post message"
        )
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.lag_report()
        assert response["status_code"] == 500
        assert (
            response["data"]
            == "External Error: Error sending message: Failed to post message"
        )

    def test_should_return_failed_report_and_post_to_slack(
        self, kafka_service, bot_fixture: BOT_FIXTURE
    ):

        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]

        local_settings = {
            "slack_bot": {
                "reports": [
                    {
                        "name": "lag_report",
                        "streams": [
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test",
                                "group_id": "test_get_lag_check_fail",
                            }
                        ],
                    }
                ]
            }
        }
        container.config.from_dict(local_settings)

        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.lag_report()
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#test-bots",
            text="""Stream Lag Report Fail
Topic: test, Group Id: test_get_lag_check_fail, Bootstrap Servers: localhost:9094, Lag: 1
""",
        )
        assert response["status_code"] == 200

    def test_should_work_with_multiple_streams(
        self, kafka_service, bot_fixture: BOT_FIXTURE
    ):
        container = bot_fixture[1]
        bot = bot_fixture[0]

        local_settings = {
            "slack_bot": {
                "reports": [
                    {
                        "name": "lag_report",
                        "streams": [
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test",
                                "group_id": "test_get_lag_multiple",
                            },
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test2",
                                "group_id": "test_get_lag_multiple",
                            },
                        ],
                    }
                ]
            }
        }
        container.config.from_dict(local_settings)

        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = bot.lag_report()
        assert len(slack_client_mock.chat_postMessage.mock_calls) == 2
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#test-bots",
            text="""Stream Lag Report Fail
Topic: test, Group Id: test_get_lag_multiple, Bootstrap Servers: localhost:9094, Lag: 1
Topic: test2, Group Id: test_get_lag_multiple, Bootstrap Servers: localhost:9094, Lag: 1
""",
        )
        assert response["status_code"] == 200


class TestDetectionsReport:
    def test_should_return_success_report_and_post_to_slack(
        self, kafka_service, psql_service, init_first_db, bot_fixture
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]

        local_settings = {
            "slack_bot": {
                "reports": [
                    {
                        "name": "detections_report",
                        "streams": [
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test",
                                "group_id": "test_detections_report_success",
                                "batch_size": 2,
                                "identifiers": ["objectId", "candid"],
                            }
                        ],
                        "database": [
                            {
                                "host": "localhost",
                                "database": "postgres",
                                "user": "postgres",
                                "password": "postgres",
                                "port": "5432",
                                "detections_table_name": "detection",
                                "detections_id_field": "candid",
                            }
                        ],
                    }
                ]
            }
        }
        container.config.from_dict(local_settings)
        init_first_db(insert=True)
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        container.slack_signature_verifier.override(providers.Factory(mock.MagicMock))
        response = scheduled_bot.detections_report()
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#test-bots",
            text="""Detections Report Success
Topic test from localhost:9094 with group id test_detections_report_success processed 1 out of 1 alerts with 0 missing
""",
        )
        assert response["status_code"] == 200

    def test_should_return_check_fail_report_and_post_to_slack(
        self, kafka_service, psql_service, init_first_db, bot_fixture
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]

        local_settings = {
            "slack_bot": {
                "reports": [
                    {
                        "name": "detections_report",
                        "streams": [
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test",
                                "group_id": "test_detections_report_fail",
                                "batch_size": 2,
                                "identifiers": ["objectId", "candid"],
                            }
                        ],
                        "database": [
                            {
                                "host": "localhost",
                                "database": "postgres",
                                "user": "postgres",
                                "password": "postgres",
                                "port": "5432",
                                "detections_table_name": "detection",
                                "detections_id_field": "candid",
                            }
                        ],
                    }
                ]
            }
        }
        container.config.from_dict(local_settings)
        init_first_db(insert=False)
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        container.slack_signature_verifier.override(providers.Factory(mock.MagicMock))
        response = scheduled_bot.detections_report()
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#test-bots",
            text="""Detections Report Failed
Topic test from localhost:9094 with group id test_detections_report_fail processed 0 out of 1 alerts with 1 missing
""",
        )
        assert response["status_code"] == 200

    def test_should_work_with_two_databases(
        self,
        kafka_service,
        psql_service,
        second_database,
        init_first_db,
        init_second_db,
        bot_fixture,
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]

        local_settings = {
            "slack_bot": {
                "reports": [
                    {
                        "name": "detections_report",
                        "streams": [
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test",
                                "group_id": "test_detections_two_database",
                                "batch_size": 2,
                                "identifiers": ["objectId", "candid"],
                            },
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test2",
                                "group_id": "test_detections_two_database_2",
                                "batch_size": 2,
                                "identifiers": ["objectId", "candid"],
                            },
                        ],
                        "database": [
                            {
                                "host": "localhost",
                                "database": "postgres",
                                "user": "postgres",
                                "password": "postgres",
                                "port": "5432",
                                "detections_table_name": "detection",
                                "detections_id_field": "candid",
                            },
                            {
                                "host": "localhost",
                                "database": "postgres",
                                "user": "postgres",
                                "password": "postgres",
                                "port": "5433",
                                "detections_table_name": "detection",
                                "detections_id_field": "candid",
                            },
                        ],
                    }
                ]
            }
        }
        container.config.from_dict(local_settings)
        init_first_db(insert=True)
        init_second_db(insert=True)
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        container.slack_signature_verifier.override(providers.Factory(mock.MagicMock))
        response = scheduled_bot.detections_report()
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#test-bots",
            text="""Detections Report Success
Topic test from localhost:9094 with group id test_detections_two_database processed 1 out of 1 alerts with 0 missing
Topic test2 from localhost:9094 with group id test_detections_two_database_2 processed 1 out of 1 alerts with 0 missing
""",
        )
        assert response["status_code"] == 200

    def test_should_work_with_two_databases_check_fail(
        self,
        kafka_service,
        psql_service,
        second_database,
        init_first_db,
        init_second_db,
        bot_fixture,
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]

        local_settings = {
            "slack_bot": {
                "reports": [
                    {
                        "name": "detections_report",
                        "streams": [
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test",
                                "group_id": "test_detections_two_database_check_fail",
                                "batch_size": 2,
                                "identifiers": ["objectId", "candid"],
                            },
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test2",
                                "group_id": "test_detections_two_database_2_check_fail",
                                "batch_size": 2,
                                "identifiers": ["objectId", "candid"],
                            },
                        ],
                        "database": [
                            {
                                "host": "localhost",
                                "database": "postgres",
                                "user": "postgres",
                                "password": "postgres",
                                "port": "5432",
                                "detections_table_name": "detection",
                                "detections_id_field": "candid",
                            },
                            {
                                "host": "localhost",
                                "database": "postgres",
                                "user": "postgres",
                                "password": "postgres",
                                "port": "5433",
                                "detections_table_name": "detection",
                                "detections_id_field": "candid",
                            },
                        ],
                    }
                ]
            }
        }
        container.config.from_dict(local_settings)
        init_first_db(insert=True)
        init_second_db(insert=False)
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        container.slack_signature_verifier.override(providers.Factory(mock.MagicMock))
        response = scheduled_bot.detections_report()
        slack_client_mock.chat_postMessage.assert_called_with(
            channel="#test-bots",
            text="""Detections Report Failed
Topic test from localhost:9094 with group id test_detections_two_database_check_fail processed 1 out of 1 alerts with 0 missing
Topic test2 from localhost:9094 with group id test_detections_two_database_2_check_fail processed 0 out of 1 alerts with 1 missing
""",
        )
        assert response["status_code"] == 200

    def test_should_work_with_two_databases_wrong_db(
        self,
        kafka_service,
        psql_service,
        init_first_db,
        bot_fixture,
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]

        local_settings = {
            "slack_bot": {
                "reports": [
                    {
                        "name": "detections_report",
                        "streams": [
                            {
                                "bootstrap_servers": "localhost:9094",
                                "topic": "test",
                                "group_id": "test_detections_wrong_db",
                                "batch_size": 2,
                                "identifiers": ["objectId", "candid"],
                            },
                        ],
                        "database": [
                            {
                                "host": "localhost",
                                "database": "postgres",
                                "user": "postgres",
                                "password": "postgres",
                                "port": "5432",
                                "detections_table_name": "not_found",
                                "detections_id_field": "candid",
                            },
                        ],
                    }
                ]
            }
        }
        container.config.from_dict(local_settings)
        init_first_db(insert=True)
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        container.slack_signature_verifier.override(providers.Factory(mock.MagicMock))
        response = scheduled_bot.detections_report()
        slack_client_mock.chat_postMessage.assert_not_called()
        assert response["status_code"] == 500
