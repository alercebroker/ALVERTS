from shared import ClientException, ExternalException
from user_interface.adapters.presenter import ReportPresenter
from modules.stream_verifier.infrastructure.response_models import (
    LagReportResponseModel,
    DetectionsReportResponseModel,
    StampClassificationsReportResponseModel,
)
from flask import Response
from slack.web.client import WebClient
from typing import Union, List, NewType, Dict
from datetime import datetime
import tzlocal

SlackParameters = NewType("SlackParameters", Dict[str, str])


class SlackExporter(ReportPresenter):
    def __init__(
        self,
        client: WebClient,
        view: Union[Response, dict] = None,
    ):
        self.client = client
        self.view = view

    def set_view(
        self,
        view: Union[Response, dict],
    ):
        self.view = view

    def set_slack_parameters(self, slack_parameters: List[SlackParameters]):
        if slack_parameters.get("channel_names") is None:
            self.handle_request_error(
                ClientException("Parameters must include channel_names")
            )
            return
        self.slack_parameters = slack_parameters

    def export_lag_report(self, report: LagReportResponseModel):
        try:
            text = self._parse_lag_report_to_string(report)
        except Exception as e:
            self.handle_application_error(ClientException(f"Error parsing report: {e}"))
            return

        post_response = self.post_to_slack(text)
        if not post_response:
            return

        if isinstance(self.view, dict):
            self.view["status_code"] = post_response.status_code
            self.view["data"] = text
        else:
            self.view.status_code = post_response.status_code
            self.view.data = text

    def export_detections_report(self, report: DetectionsReportResponseModel):
        try:
            text = self._parse_detections_report_to_string(report)
        except Exception as e:
            self.handle_application_error(ClientException(f"Error parsing report: {e}"))
            return

        post_response = self.post_to_slack(text)
        if not post_response:
            return

        if isinstance(self.view, dict):
            self.view["status_code"] = post_response.status_code
            self.view["data"] = text
        else:
            self.view.status_code = post_response.status_code
            self.view.data = text

    def export_stamp_classifications_report(
        self, report: StampClassificationsReportResponseModel
    ):
        try:
            text = self._parse_stamp_classifications_report_to_string(report)
        except Exception as e:
            self.handle_application_error(ClientException(f"Error parsing report: {e}"))
            return

        post_response = self.post_to_slack(text)
        if not post_response:
            return

        if isinstance(self.view, dict):
            self.view["status_code"] = post_response.status_code
        else:
            self.view.status_code = post_response.status_code

    def handle_client_error(self, error: ClientException):
        message = f"Client Error: {error}"
        code = 400
        if isinstance(self.view, dict):
            self.view["status_code"] = code
            self.view["data"] = message
        else:
            self.view.status_code = code
            self.view.data = message

    def handle_external_error(self, error: ExternalException):
        message = f"External Error: {error}"
        code = 500
        if isinstance(self.view, dict):
            self.view["status_code"] = code
            self.view["data"] = message
        else:
            self.view.status_code = code
            self.view.data = message

    def handle_application_error(self, error: Exception):
        message = f"Application Error: {error}"
        code = 500
        if isinstance(self.view, dict):
            self.view["status_code"] = code
            self.view["data"] = message
        else:
            self.view.status_code = code
            self.view.data = message

    def handle_request_error(self, error: Exception):
        message = f"Request Error: {error}"
        code = 400
        if isinstance(self.view, dict):
            self.view["status_code"] = code
            self.view["data"] = message
        else:
            self.view.status_code = code
            self.view.data = message

    def _parse_lag_report_to_string(self, report: LagReportResponseModel):
        if report.success:
            text = f"""Stream Lag Report Success\nNo group id has lag"""
        else:
            text = f"""Stream Lag Report Fail\n"""
            for rep in report.streams:
                text += f"Topic: {rep.topic}, Group Id: {rep.group_id}, Bootstrap Servers: {rep.bootstrap_servers}, Lag: {rep.lag}"
                text += "\n"
        return text

    def _parse_detections_report_to_string(self, report: DetectionsReportResponseModel):
        text = "Topic {} from {} with group id {} processed {} out of {} alerts with {} missing\n"
        state_text = "Success" if report.success else "Failed"
        post_message = f"Detections Report {state_text}\n"
        for rep in report.streams:
            text_copy = text
            post_message += text_copy.format(
                rep.topic,
                rep.bootstrap_servers,
                rep.group_id,
                rep.processed,
                rep.total_messages,
                len(rep.difference),
            )

        return post_message

    def _parse_stamp_classifications_report_to_string(
        self, report: StampClassificationsReportResponseModel
    ):
        tz = tzlocal.get_localzone()
        today = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %z")
        post_message = (
            f""":astronaut: :page_facing_up: ALeRCE's report of today ({today}):\n\t"""
        )

        for rep in report.databases:
            if len(rep.counts) == 0:
                post_message += f"""• Database: {rep.database}\n\t• Host: {rep.host}\n\t:red_circle: No alerts today\n\t"""

            else:
                res = ""
                for r in rep.counts:
                    res += f"\t\t\t - {r[0]:<8}: {r[1]:>7}\n"

                post_message += f"""• Database: {rep.database}\n\t• Host: {rep.host}\n\t• Objects observed last night: {rep.observed:>7} :night_with_stars:\n\t• New objects observed last night: {rep.new_objects:>7} :full_moon_with_face:\n\t• Stamp classifier distribution: \n {res}\t"""

        return post_message

    def post_to_slack(self, text: str):
        try:
            channels = self.slack_parameters.get("channel_names")
        except Exception as e:
            self.handle_client_error(
                ClientException(f"slack parameters not provided: {e}")
            )
            return
        try:
            for channel in channels:
                post_response = self.client.chat_postMessage(
                    channel=f"#{channel}", text=text
                )
        except Exception as e:
            self.handle_external_error(ExternalException(f"Error sending message: {e}"))
            return
        else:
            return post_response
