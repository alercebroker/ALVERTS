from shared import Controller, ClientException, ExternalException
from modules.stream_verifier.infrastructure.response_models import (
    LagReportResponseModel,
)
from modules.stream_verifier.infrastructure.request_models import (
    LagReportRequestModel,
)
from typing import Callable, List, Union
from modules.stream_verifier.use_cases import GetLagReport
from .slack_presenter import SlackExporter
from flask import Request, Response


class SlackController(Controller):
    def __init__(
        self,
        slack_exporter: SlackExporter,
        get_lag_report: GetLagReport,
        get_db_report,
        stream_config: List[dict],
    ):
        self.exporter = slack_exporter
        self.get_lag_report = get_lag_report
        self.stream_config = stream_config

    def get_db_count_report(self, request: Request, response: Response):
        return super().get_db_count_report(request)

    def get_stream_lag_report(self, request: Request, response: Response):
        # define callback functions
        def respond_check_success(
            report: Union[List[LagReportResponseModel], LagReportResponseModel]
        ):
            self.exporter.export_lag_report(
                report,
                slack_data,
                response,
                status="Success",
            )

        def respond_check_fail(
            report: Union[List[LagReportResponseModel], LagReportResponseModel]
        ):
            self.exporter.export_lag_report(
                report,
                slack_data,
                response,
                status="Fail",
            )

        def respond_client_error(error: ClientException):
            self.exporter.handle_client_error(error, response)

        def respond_external_error(error: ExternalException):
            self.exporter.handle_external_error(error, response)

        def respond_parse_error(error: ExternalException):
            self.exporter.handle_parse_error(error, response)

        # get slack data from the http request ensuring required parameters
        try:
            slack_data = self._get_slack_data(request)
        except AssertionError as e:
            self.exporter.handle_request_error(
                AssertionError("Wrong slack parameters"), response
            )
            return

        # get stream request model from container configuration
        try:
            request_models = [self._to_lag_request_model(x) for x in self.stream_config]
        except Exception as e:
            self.exporter.handle_client_error(e, response)
            return

        # execute the use case and let the presenter handle the rest
        self.get_lag_report.execute(
            request_models,
            {
                "respond_check_success": respond_check_success,
                "respond_check_fail": respond_check_fail,
                "respond_client_error": respond_client_error,
                "respond_external_error": respond_external_error,
                "respond_parse_error": respond_parse_error,
            },
        )

    def _to_lag_request_model(self, data: dict):
        topic = data["topic"]
        group_id = data["group_id"]
        bootstrap_servers = data["bootstrap_servers"]
        return LagReportRequestModel(
            bootstrap_servers=bootstrap_servers, group_id=group_id, topic=topic
        )

    def _get_slack_data(self, request):
        assert request.form.get("channel_name") is not None
        assert request.form.get("user_name") is not None
        return request.form
