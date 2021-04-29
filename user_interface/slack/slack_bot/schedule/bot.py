from user_interface.slack.slack_bot.settings import OLD_DATABASE_CONFIG
from user_interface.slack.slack_bot.utils import (
    queries,
    db as db_utils,
    streams as stream_utils,
)
from dependency_injector.wiring import inject, Provide
from db_plugins.db.sql import SQLConnection
from slack.errors import SlackApiError
from slack.web.client import WebClient
from typing import List
from flask import make_response
from user_interface.slack.slack_bot.container import SlackContainer
from user_interface.slack.adapters.slack_presenter import SlackExporter
from user_interface.adapters.controller import ReportController

import itertools
import logging
import schedule
import time


class ScheduledBot:
    def __init__(
        self,
        log_level="INFO",
    ):
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(log_level)

    @inject
    def stream_lag_report(
        self,
        controller: ReportController = Provide[SlackContainer.slack_controller],
        params: dict = Provide[SlackContainer.config.slack_bot],
    ):
        lag_report_params = next(
            filter(lambda report: report["name"] == "lag_report", params["reports"])
        )
        schedule_params = next(
            filter(
                lambda schedule: schedule["report"] == "lag_report", params["schedule"]
            )
        )

        request = {"channel_names": schedule_params["channels"], "user_name": "bot"}
        response = {"data": "", "status_code": 200}
        controller.presenter.set_view(response)
        controller.presenter.set_slack_parameters(request)
        if controller.presenter.view["status_code"] == 200:
            controller.get_report(lag_report_params, "lag_report")
        self.logger.info(
            f"Report: stream_lag_report, status: { response[ 'status_code' ] }, data: {response['data']}"
        )
        return response

    @inject
    def detections_report(
        self,
        channel: str,
        controller: ReportController = Provide[SlackContainer.slack_controller],
        database: list = Provide[SlackContainer.config.database],
        streams: dict = Provide[SlackContainer.stream_params_creator],
    ):
        self.logger.info("Producing detections report")
        request = {"channel_name": channel, "user_name": "bot"}
        response = {"data": "", "status_code": 200}
        controller.presenter.set_view(response)
        controller.presenter.set_slack_parameters(request)
        if controller.presenter.view["status_code"] == 200:
            params = {
                "streams": streams["stream_params_detections_report"],
                "database": database,
            }
            controller.get_report(params, "detections_report")
        self.logger.info(
            f"Report: detections_report, status: { response[ 'status_code' ] }, data: {response['data']}"
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
