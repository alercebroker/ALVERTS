from shared import ClientException, ExternalException, Presenter
from modules.stream_verifier.infrastructure.response_models import (
    LagReportResponseModel,
)
from flask import Response
from user_interface.slack.slack_bot.commands.slash import Slash
from slack.web.client import WebClient
from slack.signature.verifier import SignatureVerifier
from typing import Union, List


class SlackExporter(Presenter):
    def __init__(self, client: WebClient, signature_verifier: SignatureVerifier):
        self.client = client
        self.signature_verifier = signature_verifier

    def export_db_report(self, report):
        return super().export_db_report(report)

    def export_lag_report(
        self,
        report: Union[List[LagReportResponseModel], LagReportResponseModel],
        slack_data: dict,
        response: Response,
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
        self,
        report: Union[List[LagReportResponseModel], LagReportResponseModel],
        state: str,
    ):
        if state == "Success":
            text = f"""Stream Lag Report {state}\nNo group id has lag"""
        if state == "Fail":
            if isinstance(report, LagReportResponseModel):
                report = [report]
            text = f"""Stream Lag Report {state}\n"""
            for rep in report:
                text += rep.to_string()
        return text
