from dataclasses import dataclass, field
from shared.gateways.request_models import KafkaRequest, TableRequest
from typing import List


@dataclass
class LagReportRequestModel:
    streams: List[KafkaRequest] = field(default_factory=list)


@dataclass
class DetectionsReportRequestModel:
    streams: List[KafkaRequest] = field(default_factory=list)
    tables: List[TableRequest] = field(default_factory=list)

    def params(self):
        for i, stream in enumerate(self.streams):
            yield stream, self.tables[i]
