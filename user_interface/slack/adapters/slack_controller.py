from shared import Controller, ClientException, ExternalException
from shared.gateways.request_models import StreamRequestModel
from modules.stream_verifier.domain import LagReport
from typing import Callable, List, Union
from modules.stream_verifier.use_cases import GetLagReport


class SlackController(Controller):
    def __init__(
        self,
        slack_exporter,
        get_lag_report: GetLagReport,
        get_candid_count_report,
        stream_config: List[dict],
    ):
        self.exporter = slack_exporter
        self.get_lag_report = get_lag_report
        self.stream_config = stream_config

    def get_db_count_report(self, request_model):
        return super().get_db_count_report(request_model)

    def get_stream_lag_report(self, request: dict, response):
        # define callback functions
        def respond_check_success(report: Union[List[LagReport], LagReport]):
            self.exporter.export_report(report, slack_data, response)

        def respond_check_fail(report: Union[List[LagReport], LagReport]):
            self.exporter.export_report_fail(report, slack_data, response)

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
            request_models = [self._to_request_model(x) for x in self.stream_config]
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

    def _to_request_model(self, data: dict):
        topic = data["topic"]
        group_id = data["group_id"]
        bootstrap_servers = data["bootstrap_servers"]
        StreamRequestModel(
            bootstrap_servers=bootstrap_servers, group_id=group_id, topic=topic
        )

    def _get_slack_data(self, request):
        assert request.form.get("channel_name") != None
        assert request.form.get("user_name") != None
        return request.form
