from user_interface.slack.slack_bot.settings import DATABASE
from user_interface.slack.slack_bot.utils import queries
from user_interface.slack.slack_bot.utils.db import session_options
from db_plugins.db.sql import SQLConnection


class Slash:
    def __init__(self):
        self.db = SQLConnection()
        self.db.connect(
            config=DATABASE["SQL"], session_options=session_options, use_scoped=True
        )

    def get_last_night_objects(self, channel=None, user=None):
        welcome = ""
        if channel:
            welcome += f"Hi #{channel}"
        if user:
            welcome += f" (asked by {user})"
        response = queries.get_last_night_objects(self.db)
        return f"{welcome}\n{response}"
