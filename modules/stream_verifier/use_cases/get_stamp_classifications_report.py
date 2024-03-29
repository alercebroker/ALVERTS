from modules.stream_verifier.infrastructure import StreamVerifier
from modules.stream_verifier.infrastructure.request_models import StampClassificationsReportRequestModel
from modules.stream_verifier.infrastructure.response_models import (
    StampClassificationsReportResponseModel,
)
from typing import Dict, Callable
from shared import ClientException, ExternalException, Result, UseCase

class GetStampClassificationsReport(UseCase):
    def __init__(self, verifier: StreamVerifier):
        self.verifier = verifier

    def execute(
        self, request_model: StampClassificationsReportRequestModel, callbacks: Dict[str, Callable]
    ):
        result: Result[
            StampClassificationsReportResponseModel, Exception
        ] = self.verifier.get_stamp_classifications_report(request_model)

        if result.success:
            callbacks["success"](result.value)
        else:
            if type(result.error) == ClientException:
                callbacks["client_error"](result.error)
            elif type(result.error) == ExternalException:
                callbacks["external_error"](result.error)
            else:
                callbacks["application_error"](result.error)
