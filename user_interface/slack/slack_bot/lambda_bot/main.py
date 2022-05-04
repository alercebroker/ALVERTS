from user_interface.slack.slack_bot.lambda_bot import bot
from dependency_injector import providers
from shared.gateways.__tests__.kafka.mocks import MockKafkaService
from shared.gateways.__tests__.psql.mocks import MockPsqlService
from user_interface.slack.slack_bot.container import SlackContainer
import sys

def main_function():
    container = SlackContainer()
    container.config.from_yaml("user_interface/slack/slack_bot/settings.yml")
    container.wire(modules=[sys.modules[bot.__name__]])
    lambda_bot = bot.LambdaBot()
    lambda_bot.run()
