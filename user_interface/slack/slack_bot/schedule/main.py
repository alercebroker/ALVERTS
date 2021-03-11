from .bot import ScheduledBot
from user_interface.slack.slack_bot.settings import (
    SLACK_SCHEDULE_CONFIG,
    ALERT_SYSTEM_CONFIG,
)
from core.alert_system import AlertSystem

alert_system = AlertSystem(ALERT_SYSTEM_CONFIG)
scheduled_bot = ScheduledBot(SLACK_SCHEDULE_CONFIG, alert_system)

scheduled_bot.schedule()
scheduled_bot.run()
