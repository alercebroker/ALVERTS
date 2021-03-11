from user_interface.slack.slack_bot.settings import DATABASE
from user_interface.slack.slack_bot.utils import queries
from user_interface.slack.slack_bot.utils.db import session_options
from core.alert_system import AlertSystem
from db_plugins.db.sql import SQLConnection
from slack.errors import SlackApiError
from slack.web.client import WebClient
from typing import List
from flask import make_response

import itertools
import logging
import schedule
import time


class ScheduledBot:
    def __init__(
        self, alert_system: AlertSystem, config: dict, log_level="INFO", db_conn=None
    ):
        self._init_log(log_level)
        self.alert_system = alert_system
        self.db = db_conn or SQLConnection()
        self.db.connect(
            config=DATABASE["SQL"], session_options=session_options, use_scoped=True
        )
        self.config = config

    def _init_log(self, level) -> None:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(level)

    def _send_message(self, channel: str, text: str) -> None:
        try:
            self.alert_system.container.slack_client.chat_postMessage(
                channel=channel, text=text
            )
        except SlackApiError as e:
            self.logger.error(
                f"Request to Slack API Failed: {e.response.status_code} - {e.response}"
            )

    def last_night_stats(self, channel: str) -> None:
        last_night_report = queries.get_last_night_objects(self.db)
        self._send_message(channel, last_night_report)
        self.logger.info("Report sent: last_night_stats")

    def stream_lag_report(self, channel: str):
        slack_controller = self.alert_system.get_controller("slack")
        request = {"channel_name": channel, "user_name": "bot"}
        response = {"data": "", "status_code": 200}
        slack_controller.get_stream_lag_report(request, response)
        self.logger.info(
            f"Report: stream_lag_report, status: { response[ 'status_code' ] }, data: {response['data']}"
        )

    def schedule(self) -> List:
        self.logger.info("Scheduling messages")
        channels_scheduled = []
        if "every_day" in self.config.keys():
            for k, v in self.config["every_day"].items():
                channels_scheduled = list(
                    itertools.product(v["schedule"], v["channels"])
                )
                for cs in channels_scheduled:
                    self.logger.info(f"{k} every day at {cs[0]} to {cs[1]}")
                    method = getattr(self, k)
                    schedule.every().day.at(cs[0]).do(lambda: method(cs[1]))
        return channels_scheduled

    def run(self) -> None:
        self.logger.info("Running schedule")
        while True:
            schedule.run_pending()
            time.sleep(5)
