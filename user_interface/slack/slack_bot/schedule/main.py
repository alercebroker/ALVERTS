from user_interface.slack.slack_bot.schedule import bot
from dependency_injector import providers
from shared.gateways.__tests__.kafka.mocks import MockKafkaService
from shared.gateways.__tests__.psql.mocks import MockPsqlService
from user_interface.slack.slack_bot.container import SlackContainer
from user_interface.slack.slack_bot import settings
import sys

container = SlackContainer()
container.db_service.override(providers.Factory(MockPsqlService, state="success"))
container.kafka_service.override(providers.Factory(MockKafkaService, state="success"))
container.config.from_dict(
    {
        "slack": settings.SLACK_CREDENTIALS,
        "streams": settings.KAFKA_STREAMS,
        "database": settings.DATABASE_CONFIG,
    }
)
container.wire(modules=[sys.modules[bot.__name__]])
scheduled_bot = bot.ScheduledBot(settings.SLACK_SCHEDULE_CONFIG)

scheduled_bot.schedule()
scheduled_bot.run()
