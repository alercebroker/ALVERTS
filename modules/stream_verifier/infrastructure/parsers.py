from modules.stream_verifier.domain.lag_report import LagReport
from shared import Result
from .utils.utils import LagResponseModel


class StreamLagParser:
    def to_report(self, resp: LagResponseModel):
        report = LagReport(topic=resp.topic, lags=resp.lags)
        success = report.total_lag() == 0
        return Result.Ok(report, check_success=success)
