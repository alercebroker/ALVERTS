import pytest
from unittest import mock
from user_interface.slack.slack_bot.schedule import bot
from user_interface.slack.slack_bot.container import SlackContainer
from typing import List, NewType, Tuple
from shared.result.result import Result
from modules.stream_verifier.domain.lag_report import LagReport
from shared.error.exceptions import ClientException, ExternalException
from dependency_injector import providers
from shared.gateways.__tests__.kafka.mocks import MockKafkaService
from shared.gateways.__tests__.psql.mocks import MockPsqlService
import sys
import logging
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


class TestStreamLagReport:
    def test_should_return_success_report_and_post_to_slack(
        self, bot_fixture: BOT_FIXTURE
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.lag_report()
        slack_client_mock.chat_postMessage.assert_called_once_with(
            channel="#test-bots",
            text="""Stream Lag Report Success\nNo group id has lag""",
        )
        assert response["status_code"] == 200

    def test_should_return_success_report_and_fail_post_to_slack(
        self, bot_fixture: BOT_FIXTURE
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
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
        self, bot_fixture: BOT_FIXTURE
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="check_fail")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.lag_report()
        date = datetime.datetime.today()
        date = date.strftime("%Y%m%d")
        slack_client_mock.chat_postMessage.assert_called_once_with(
            channel="#test-bots",
            text="""Stream Lag Report Fail
Topic: ztf_%s_test, Group Id: xmatch, Bootstrap Servers: localhost:9094, Lag: 10
"""
            % date,
        )
        assert response["status_code"] == 200

    def test_should_return_errored_report_and_not_post_to_slack(
        self, bot_fixture: BOT_FIXTURE
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="client_error")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.lag_report()
        slack_client_mock.chat_postMessage.assert_not_called()
        assert response["status_code"] == 400

    def test_should_work_with_multiple_streams(self, bot_fixture: BOT_FIXTURE):
        container = bot_fixture[1]
        bot = bot_fixture[0]
        container.config.from_yaml(
            "user_interface/slack/slack_bot/schedule/__tests__/settings_multiple_streams.yml"
        )
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = bot.lag_report()
        slack_client_mock.chat_postMessage.assert_called_once()
        assert response["status_code"] == 200


class TestStreamDetectionsReport:
    def test_should_return_success_report_and_post_to_slack(self, bot_fixture):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        container.db_service.override(
            providers.Factory(MockPsqlService, state="success")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.detections_report()
        date = datetime.datetime.today()
        date1 = date.strftime("%Y%m%d")
        date2 = date.strftime("%Y%m%d%H%M%S")
        slack_client_mock.chat_postMessage.assert_called_once_with(
            channel="#test-bots",
            text=f"""Detections Report Success
Topic ztf_{date1}_test from localhost:9094 with group id bot_{date2} processed 2 out of 2 alerts with 0 missing
""",
        )
        assert response["status_code"] == 200

    def test_should_return_success_report_and_fail_post_to_slack(
        self, bot_fixture: BOT_FIXTURE
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        container.db_service.override(
            providers.Factory(MockPsqlService, state="success")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.side_effect = Exception(
            "Failed to post message"
        )
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.detections_report()
        assert response["status_code"] == 500
        assert (
            response["data"]
            == "External Error: Error sending message: Failed to post message"
        )

    def test_should_return_failed_report_and_post_to_slack(
        self, bot_fixture: BOT_FIXTURE
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        container.db_service.override(
            providers.Factory(MockPsqlService, state="check_fail")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.detections_report()
        date = datetime.datetime.today()
        date1 = date.strftime("%Y%m%d")
        date2 = date.strftime("%Y%m%d%H%M%S")
        slack_client_mock.chat_postMessage.assert_called_once_with(
            channel="#test-bots",
            text=f"""Detections Report Failed
Topic ztf_{date1}_test from localhost:9094 with group id bot_{date2} processed 0 out of 2 alerts with 2 missing
""",
        )
        assert response["status_code"] == 200

    def test_should_return_db_error_report_and_not_post_to_slack(
        self, bot_fixture: BOT_FIXTURE
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        container.db_service.override(
            providers.Factory(MockPsqlService, state="external_error")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.detections_report()
        slack_client_mock.chat_postMessage.assert_not_called()
        assert response["status_code"] == 500

    def test_should_return_kafka_error_report_and_not_post_to_slack(
        self, bot_fixture: BOT_FIXTURE
    ):
        container = bot_fixture[1]
        scheduled_bot = bot_fixture[0]
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="external_error")
        )
        container.db_service.override(
            providers.Factory(MockPsqlService, state="success")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = scheduled_bot.detections_report()
        slack_client_mock.chat_postMessage.assert_not_called()
        assert response["status_code"] == 500

    def test_should_work_with_multiple_streams(self, bot_fixture: BOT_FIXTURE):
        container = bot_fixture[1]
        bot = bot_fixture[0]
        container.config.from_yaml(
            "user_interface/slack/slack_bot/schedule/__tests__/settings_multiple_streams.yml"
        )
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        container.db_service.override(
            providers.Factory(MockPsqlService, state="success")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = bot.detections_report()
        date = datetime.datetime.today()
        date1 = date.strftime("%Y%m%d")
        date2 = date.strftime("%Y%m%d%H%M%S")
        print(slack_client_mock.chat_postMessage.mock_calls)
        slack_client_mock.chat_postMessage.assert_called_once_with(
            channel="#test-bots",
            text=f"""Detections Report Success
Topic ztf_{date1}_test from localhost:9094 with group id xmatch{date2} processed 2 out of 2 alerts with 0 missing
Topic ztf_{date1}_test_2 from localhost:9094 with group id correction{date2} processed 2 out of 2 alerts with 0 missing
""",
        )
        assert response["status_code"] == 200

    def test_should_work_with_multiple_channels(self, bot_fixture: BOT_FIXTURE):
        container = bot_fixture[1]
        bot = bot_fixture[0]
        container.config.from_yaml(
            "user_interface/slack/slack_bot/schedule/__tests__/settings_multiple_channels.yml"
        )
        container.kafka_service.override(
            providers.Factory(MockKafkaService, state="success")
        )
        container.db_service.override(
            providers.Factory(MockPsqlService, state="success")
        )
        slack_client_mock = mock.MagicMock()
        slack_client_mock.chat_postMessage.return_value.status_code = 200
        container.slack_client.override(providers.Object(slack_client_mock))
        response = bot.detections_report()
        date = datetime.datetime.today()
        date1 = date.strftime("%Y%m%d")
        date2 = date.strftime("%Y%m%d%H%M%S")
        slack_client_mock.chat_postMessage.assert_any_call(
            channel="#test-bots",
            text=f"""Detections Report Success
Topic ztf_{date1}_test from localhost:9094 with group id xmatch{date2} processed 2 out of 2 alerts with 0 missing
Topic ztf_{date1}_test_2 from localhost:9094 with group id correction{date2} processed 2 out of 2 alerts with 0 missing
""",
        )
        slack_client_mock.chat_postMessage.assert_any_call(
            channel="#test-bots2",
            text=f"""Detections Report Success
Topic ztf_{date1}_test from localhost:9094 with group id xmatch{date2} processed 2 out of 2 alerts with 0 missing
Topic ztf_{date1}_test_2 from localhost:9094 with group id correction{date2} processed 2 out of 2 alerts with 0 missing
""",
        )
        assert response["status_code"] == 200
