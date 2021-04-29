from user_interface.slack.slack_bot.schedule import bot
from dependency_injector import providers
from shared.gateways.__tests__.kafka.mocks import MockKafkaService
from shared.gateways.__tests__.psql.mocks import MockPsqlService
from user_interface.slack.slack_bot.container import SlackContainer
import sys

container = SlackContainer()
container.config.from_yaml("settings.yml")
container.wire(modules=[sys.modules[bot.__name__]])
scheduled_bot = bot.ScheduledBot()

scheduled_bot.schedule()
scheduled_bot.run()
