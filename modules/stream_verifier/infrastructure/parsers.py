from modules.stream_verifier.domain.lag_report import LagReport
from modules.stream_verifier.domain.detections_report import DetectionsReport
from modules.stream_verifier.domain.stamp_classifications_report import StampClassificationsReport
from .response_models import LagReportResponseModel, StreamResponse
from shared import Result
from shared.gateways.response_models import KafkaResponse
from typing import List
from modules.stream_verifier.infrastructure.response_models import (
    DetectionsReportResponseModel,
    DifferenceResponse,
    StampClassificationsReportResponseModel
)


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

    def to_detections_report(
        self, db_resp: List, kafka_resp: KafkaResponse
    ) -> Result[DetectionsReport, Exception]:
        try:
            report = DetectionsReport(
                bootstrap_servers=kafka_resp.bootstrap_servers,
                topic=kafka_resp.topic,
                group_id=kafka_resp.group_id,
                difference=db_resp,
                total_alerts=len(kafka_resp.data),
            )
            return Result.Ok(report)
        except Exception as e:
            return Result.Fail(e)
    
    def to_stamp_classifications_report(
        self, db_resp: List
    ) -> Result[StampClassificationsReport, Exception]:
        
        try:            
            report = StampClassificationsReport(
                counts= db_resp
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

    def to_detections_report_response_model(
        self, reports: List[DetectionsReport]
    ) -> Result[DetectionsReportResponseModel, Exception]:
        success = True
        diffs: List[DifferenceResponse] = []
        total_messages = 0
        processed = 0
        try:
            for report in reports:
                updated = False
                for diff in diffs:
                    if (
                        diff.bootstrap_servers == report.bootstrap_servers
                        and diff.topic == report.topic
                        and diff.group_id == report.group_id
                    ):
                        updated = True
                        diff.difference.extend(report.difference)
                        diff.total_messages += report.total_alerts
                        diff.processed += report.processed_alerts()
                if not updated:
                    diffs.append(
                        DifferenceResponse(
                            report.bootstrap_servers,
                            report.group_id,
                            report.topic,
                            report.difference,
                            report.total_alerts,
                            report.processed_alerts(),
                        )
                    )
                success = report.check_success()
            return Result.Ok(
                DetectionsReportResponseModel(streams=diffs, success=success)
            )
        except Exception as e:
            return Result.Fail(e)
    
    def to_stamp_classifications_report_response_model(
        self, db_url: str, report: StampClassificationsReport
    ) -> Result[StampClassificationsReportResponseModel, Exception]:

        success = True
        try:
            return Result.Ok(StampClassificationsReportResponseModel(
                                counts = report.counts,
                                db_url = db_url,
                                success = success
            ))
        except Exception as e:
            return Result.Fail(e)


        
        
        

        