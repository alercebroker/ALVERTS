from dataclasses import dataclass, field
from shared.gateways.request_models import KafkaRequest
from typing import List, Dict


@dataclass
class LagReportRequestModel:
    streams: List[KafkaRequest] = field(default_factory=list)


@dataclass
class DetectionsTableRequest:
    db_url: str
    table_name: str
    id_field: str


@dataclass
class DetectionsStreamRequest(KafkaRequest):
    identifiers: List[str] = field(default_factory=list)


@dataclass
class DetectionsReportRequestModel:
    streams: List[DetectionsStreamRequest] = field(default_factory=list)
    tables: List[DetectionsTableRequest] = field(default_factory=list)

    def params(self):
        for i, stream in enumerate(self.streams):
            yield stream, self.tables[i]


@dataclass
class StampClassificationsReportRequestModel:
    db_url: str
    table_names: List[str]
    mjd_name: str
