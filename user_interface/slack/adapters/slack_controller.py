from shared import Controller, ClientException, ExternalException
from modules.stream_verifier.infrastructure.utils.utils import StreamRequestModel
from modules.stream_verifier.domain import LagReport
from typing import Callable, List
from modules.stream_verifier.use_cases import GetLagReport


class SlackController(Controller):
    def __init__(
        self,
        slack_exporter,
        get_lag_report: GetLagReport,
        get_candid_count_report: Callable,
    ):
        self.exporter = slack_exporter
        self.get_lag_report = get_lag_report

    def get_db_count_report(self, request_model):
        return super().get_db_count_report(request_model)

    def get_stream_lag_report(self, data: List[dict]):
        request_models = [self._to_request_model(x) for x in data]

        def respond_check_success(report: LagReport):
            self.exporter.export_report(report)

        def respond_check_fail(report: LagReport):
            self.exporter.export_report(report)

        def respond_client_error(error: ClientException):
            self.exporter.handle_client_error(error)

        def respond_external_error(error: ExternalException):
            self.exporter.handle_external_error(error)

        def respond_parse_error(error: ExternalException):
            self.exporter.handle_parse_error(error)

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

    def _to_request_model(self, data: dict):
        try:
            topic = data["topic"]
            group_id = data["group_id"]
            bootstrap_servers = data["bootstrap_servers"]
        except KeyError as e:
            self.exporter.handle_request_error(e)

        try:
            StreamRequestModel(
                bootstrap_servers=bootstrap_servers, group_id=group_id, topic=topic
            )
        except Exception as e:
            self.exporter.handle_request_error(e)
