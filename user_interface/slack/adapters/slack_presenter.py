from modules.stream_verifier.domain import LagReport
from shared import ClientException, ExternalException, Presenter


class SlackExporter(Presenter):
    def export_report(self, report: LagReport):
        return report

    def handle_client_error(self, error: ClientException):
        return error

    def handle_external_error(self, error: ExternalException):
        return error

    def handle_parse_error(self, error: Exception):
        return error

    def handle_request_error(self, error: Exception):
        return error
