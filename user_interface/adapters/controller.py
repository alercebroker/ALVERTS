from .presenter import ReportPresenter
from shared import UseCase
from typing import Dict, Any, Union, List
from .request_model_creator import RequestModelCreator
from modules.stream_verifier.infrastructure.response_models import (
    LagReportResponseModel,
)


class ReportController:
    def __init__(
        self,
        presenter: ReportPresenter,
        use_cases: Dict[str, UseCase],
        request_model_creator=RequestModelCreator,
    ):
        self.presenter = presenter
        self.use_cases = use_cases
        self.request_model_creator = request_model_creator

    def get_report(self, params: Any, report_type: str):
        callbacks = self._make_callbacks(report_type)
        print(params)
        try:
            request_model = self.request_model_creator.to_request_model(
                params, report_type
            )
        except KeyError as e:
            callbacks["client_error"](Exception(f"Missing {e} parameter for streams"))
            return
        self.use_cases.get(report_type).execute(request_model, callbacks)

    def _make_callbacks(self, report_type: str):
        def on_client_error(error: Exception):
            self.presenter.handle_client_error(error)

        def on_external_error(error: Exception):
            self.presenter.handle_external_error(error)

        def on_application_error(error: Exception):
            self.presenter.handle_application_error(error)

        if report_type == "lag_report":

            def on_success(response_model: LagReportResponseModel):
                self.presenter.export_lag_report(response_model)

            callbacks = {
                "success": on_success,
                "client_error": on_client_error,
                "external_error": on_external_error,
                "application_error": on_application_error,
            }

            return callbacks
        if report_type == "detections_report":

            def on_success(response_model: LagReportResponseModel):
                self.presenter.export_detections_report(response_model)

            callbacks = {
                "success": on_success,
                "client_error": on_client_error,
                "external_error": on_external_error,
                "application_error": on_application_error,
            }

            return callbacks
