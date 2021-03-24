import os
import logging

from flask import Flask, request, make_response, current_app, Blueprint, Request
from slack.web.client import WebClient
from slack.errors import SlackApiError
from slack.signature import SignatureVerifier

from user_interface.slack.slack_bot.commands.slash import Slash
from user_interface.slack.slack_bot import settings
from user_interface.slack.slack_bot.container import SlackContainer
from user_interface.slack.adapters.slack_presenter import SlackExporter
from user_interface.adapters.controller import ReportController
from user_interface.slack.slack_bot.utils import streams as stream_utils

from dependency_injector.wiring import inject, Provide
import sys
from typing import Callable

main = Blueprint("slack", __name__, url_prefix="/slack")


def create_app():
    container = SlackContainer()
    container.config.from_dict(
        {
            "slack": settings.SLACK_CREDENTIALS,
            "database": settings.DATABASE_CONFIG,
        }
    )
    container.wire(modules=[sys.modules[__name__]])
    app = Flask(__name__)
    app.register_blueprint(main)
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    app.commander = Slash()
    app.container = container
    return app


@main.route("/", methods=["GET"])
def home():
    return make_response("Hello", 200)


@main.route("/last_night_objects", methods=["POST"])
def command_last_night_objects():
    info = request.form
    try:
        logging.info(info)
        channel = info["channel_name"]
        user = info["user_name"]
        text = current_app.commander.get_last_night_objects(channel, user)
        response = current_app.container.slack_client.chat_postMessage(
            channel=f"#{channel}", text=text
        )
    except SlackApiError as e:
        logging.error("Request to Slack API Failed: {}.".format(e.response))
        return make_response("", e.response)
    return make_response("", response.status_code)


@main.route("/stream_lag_check", methods=["POST"])
@inject
def command_stream_lag_check(
    controller: ReportController = Provide[SlackContainer.slack_controller],
    streams: dict = Provide[SlackContainer.stream_params_creator],
):
    local_request: Request = request
    controller.presenter.set_view(make_response())
    controller.presenter.set_slack_parameters(local_request.form)
    if controller.presenter.view.status_code == 200:
        controller.get_report(streams["stream_params_lag_report"], "lag_report")
    return controller.presenter.view


@main.route("/stream_detections_check", methods=["POST"])
@inject
def command_stream_detections_check(
    controller: ReportController = Provide[SlackContainer.slack_controller],
    database: list = Provide[SlackContainer.config.database],
    streams: Callable = Provide[SlackContainer.stream_params_creator],
):
    local_request: Request = request
    controller.presenter.set_view(make_response())
    controller.presenter.set_slack_parameters(local_request.form)
    params = {
        "streams": streams["stream_params_detections_report"],
        "database": database,
    }
    if controller.presenter.view.status_code == 200:
        controller.get_report(params, "detections_report")
    return controller.presenter.view


if __name__ == "__main__":
    app = create_app()
    app.run()
