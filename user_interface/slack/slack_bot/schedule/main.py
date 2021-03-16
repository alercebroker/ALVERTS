from user_interface.slack.slack_bot.schedule.bot import ScheduledBot
from user_interface.slack.slack_bot.settings import (
    SLACK_SCHEDULE_CONFIG,
    ALERT_SYSTEM_CONFIG,
)
from core.alert_system import AlertSystem
from dependency_injector import providers
from shared.gateways.__tests__.kafka.mocks import MockKafkaService

alert_system = AlertSystem(ALERT_SYSTEM_CONFIG)
alert_system.container.kafka_service.override(
    providers.Factory(MockKafkaService, state="success")
)
scheduled_bot = ScheduledBot(alert_system, SLACK_SCHEDULE_CONFIG)

scheduled_bot.schedule()
scheduled_bot.run()
