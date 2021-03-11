from modules.stream_verifier.domain.lag_report import LagReport
from .response_models import LagReportResponseModel
from shared import Result
from shared.gateways.response_models import KafkaResponse


class StreamLagParser:
    def to_report(self, resp: KafkaResponse):
        report = LagReport(
            topic=resp.topic, lags=resp.data["lags"], group_id=resp.group_id
        )
        success = report.total_lag() == 0
        report = LagReportResponseModel(
            topic=report.topic,
            group_id=report.group_id,
            lags=report.lags,
            success=success,
        )
        return Result.Ok(report, check_success=success)
