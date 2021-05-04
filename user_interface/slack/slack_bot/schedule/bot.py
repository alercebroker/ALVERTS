from dependency_injector.wiring import inject, Provide
from slack.errors import SlackApiError
from slack.web.client import WebClient
from typing import List
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
    def lag_report(
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
        controller: ReportController = Provide[SlackContainer.slack_controller],
        params: dict = Provide[SlackContainer.config.slack_bot],
    ):
        self.logger.info("Producing detections report")
        detections_report_params = next(
            filter(
                lambda report: report["name"] == "detections_report", params["reports"]
            )
        )
        schedule_params = next(
            filter(
                lambda schedule: schedule["report"] == "detections_report",
                params["schedule"],
            )
        )
        request = {"channel_names": schedule_params["channels"], "user_name": "bot"}
        response = {"data": "", "status_code": 200}
        controller.presenter.set_view(response)
        controller.presenter.set_slack_parameters(request)
        if controller.presenter.view["status_code"] == 200:
            controller.get_report(detections_report_params, "detections_report")
        self.logger.info(
            f"Report: detections_report, status: { response[ 'status_code' ] }, data: {response['data']}"
        )
        return response

    @inject
    def schedule(self, params: dict = Provide[SlackContainer.config.slack_bot]) -> List:
        self.logger.info("Scheduling messages")
        for rep in params["schedule"]:
            if rep["period"] == "every_day":
                method = getattr(self, rep["report"])
                for t in rep["times"]:
                    self.logger.info(
                        f"{rep['report']} every day at {t} to channels: {rep['channels']}"
                    )
                    schedule.every().day.at(t).do(method)

    def run(self) -> None:
        self.logger.info("Running schedule")
        while True:
            schedule.run_pending()
            time.sleep(5)
