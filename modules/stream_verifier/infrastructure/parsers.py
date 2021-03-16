from modules.stream_verifier.domain.lag_report import LagReport
from .response_models import LagReportResponseModel, StreamResponse
from shared import Result
from shared.gateways.response_models import KafkaResponse
from typing import List


class EntityParser:
    def to_lag_report(self, resp: KafkaResponse) -> Result[LagReport, Exception]:
        try:
            report = LagReport(
                bootstrap_servers=resp.bootstrap_servers,
                topic=resp.topic,
                lags=resp.data["lags"],
                group_id=resp.group_id,
            )
            return Result.Ok(report)
        except Exception as e:
            return Result.Fail(e)


class ResponseModelParser:
    def to_lag_report_response_model(
        self, reports: List[LagReport]
    ) -> Result[LagReportResponseModel, Exception]:
        success = True
        streams = []
        try:
            for report in reports:
                streams.append(
                    StreamResponse(
                        report.bootstrap_servers,
                        report.group_id,
                        report.topic,
                        report.total_lag(),
                    )
                )
                success = report.check_success()
            return Result.Ok(LagReportResponseModel(streams=streams, success=success))
        except Exception as e:
            return Result.Fail(e)
