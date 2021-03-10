from modules.stream_verifier.infrastructure import StreamVerifier
from shared.gateways.request_models import StreamRequestModel
from typing import List
from shared import ClientException, ExternalException, Result, UseCase


class GetLagReport(UseCase):
    def __init__(self, verifier: StreamVerifier):
        self.verifier = verifier

    def execute(
        self, request_models: List[StreamRequestModel], callbacks: dict
    ) -> Result:
        result = self.verifier.get_lag_report(request_models)

        if result.success:
            if result.check_success:
                callbacks["respond_check_success"](result.value)
            else:
                callbacks["respond_check_fail"](result.value)
        else:
            if type(result.error) == ClientException:
                callbacks["respond_client_error"](result.error)
            elif type(result.error) == ExternalException:
                callbacks["respond_external_error"](result.error)
            else:
                callbacks["respond_parse_error"](result.error)
