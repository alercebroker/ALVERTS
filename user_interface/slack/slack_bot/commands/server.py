import os
import logging

from flask import Flask, request, make_response, current_app, Blueprint
from slack.web.client import WebClient
from slack.errors import SlackApiError
from slack.signature import SignatureVerifier

from user_interface.slack.slack_bot.commands.slash import Slash
from core.alert_system import AlertSystem
from user_interface.slack.slack_bot import settings

main = Blueprint("slack", __name__, url_prefix="/slack")


def create_app():
    dict_config = settings.ALERT_SYSTEM_CONFIG
    alert_system = AlertSystem(dict_config)
    app = Flask(__name__)
    app.register_blueprint(main)
    app.alert_system = alert_system
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    app.commander = Slash()
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
        response = current_app.alert_system.container.slack_client.chat_postMessage(
            channel=f"#{channel}", text=text
        )
    except SlackApiError as e:
        print(e)
        logging.error("Request to Slack API Failed: {}.".format(e.response))
        return make_response("", e.response)
    return make_response("", response.status_code)


@main.route("/stream_lag_check", methods=["POST"])
def command_stream_lag_check():
    slack_controller = current_app.alert_system.get_controller("slack")
    response = make_response()
    slack_controller.get_stream_lag_report(request, response)
    return response


if __name__ == "__main__":
    app = create_app()
    app.run()
