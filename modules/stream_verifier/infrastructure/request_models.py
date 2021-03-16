from dataclasses import dataclass, field
from shared.gateways.kafka import KafkaRequest
from typing import List


@dataclass
class LagReportRequestModel:
    streams: List[KafkaRequest] = field(default_factory=list)
