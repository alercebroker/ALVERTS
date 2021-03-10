from shared import ClientException, ExternalException, Presenter
from modules.stream_verifier.domain import LagReport
from flask import make_response
from user_interface.slack.slack_bot.commands.slash import Slash
from slack.web.client import WebClient
from slack.signature.verifier import SignatureVerifier
from typing import Union, List


class SlackExporter(Presenter):
    def __init__(self, client: WebClient, signature_verifier: SignatureVerifier):
        self.client = client
        self.signature_verifier = signature_verifier

    def export_report(self, report, slack_data: dict, response):
        if isinstance(report, list):
            if isinstance(report[0], LagReport):
                self.export_lag_report(report, slack_data, response, "Success")
        else:
            if isinstance(report, LagReport):
                self.export_lag_report(report, slack_data, response, "Success")

    def export_report_fail(self, report, slack_data: dict, response):
        if isinstance(report, list):
            if isinstance(report[0], LagReport):
                self.export_lag_report(report, slack_data, response, "Fail")
        else:
            if isinstance(report, LagReport):
                self.export_lag_report(report, slack_data, response, "Fail")

    def export_lag_report(
        self,
        report: Union[List[LagReport], LagReport],
        slack_data: dict,
        response,
        status: str,
    ):
        channel = slack_data.get("channel_name")
        text = self._parse_lag_report_to_string(report, status)
        post_response = self.client.chat_postMessage(channel=f"#{channel}", text=text)
        response.status_code = post_response.status_code

    def handle_client_error(self, error: ClientException, response):
        response.data = f"Client Error: {error}"
        response.status_code = 400

    def handle_external_error(self, error: ExternalException, response):
        response.data = f"External Error: {error}"
        response.status_code = 500

    def handle_parse_error(self, error: Exception, response):
        response.data = f"Parse Error: {error}"
        response.status_code = 500

    def handle_request_error(self, error: Exception, response):
        response.data = f"Request Error: {error}"
        response.status_code = 400

    def _parse_lag_report_to_string(
        self, report: Union[List[LagReport], LagReport], state: str
    ):
        if isinstance(report, LagReport):
            text = f"""Stream Lag Report {state}:
            topic: {report.topic}
            lag: {sum(report.lags)}"""
        else:
            text = "Stream Lag Report {state}"
            for rep in report:
                text += f"""topic: {report.topic}
                lag: {sum(rep.lags)}"""
                text += "\n"
        return text
