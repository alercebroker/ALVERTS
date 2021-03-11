from dataclasses import dataclass
from shared.gateways.kafka import KafkaRequest


@dataclass
class LagReportRequestModel(KafkaRequest):
    topic: str
    group_id: str
    bootstrap_servers: str
