from dataclasses import dataclass


@dataclass
class KafkaRequest:
    bootstrap_servers: str
    group_id: str
    topic: str
