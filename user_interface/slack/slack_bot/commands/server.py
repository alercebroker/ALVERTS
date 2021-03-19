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

from dependency_injector.wiring import inject, Provide
import sys

main = Blueprint("slack", __name__, url_prefix="/slack")


def create_app():
    container = SlackContainer()
    container.config.from_dict(
        {
            "slack": settings.SLACK_CREDENTIALS,
            "streams": settings.KAFKA_STREAMS,
            "db": {"table_identifiers": ["oid", "candid"]},
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
        print(e)
        logging.error("Request to Slack API Failed: {}.".format(e.response))
        return make_response("", e.response)
    return make_response("", response.status_code)


@main.route("/stream_lag_check", methods=["POST"])
@inject
def command_stream_lag_check(
    controller: ReportController = Provide[SlackContainer.slack_controller],
    exporter: SlackExporter = Provide[SlackContainer.slack_exporter],
    streams: dict = Provide[SlackContainer.config.streams],
):
    local_request: Request = request
    exporter.set_view(make_response())
    exporter.set_slack_parameters(local_request.form)
    if exporter.view.status_code == 200:
        controller.get_report(streams, "lag_report")
    return exporter.view


if __name__ == "__main__":
    app = create_app()
    app.run()
