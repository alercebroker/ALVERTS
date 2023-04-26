from dataclasses import dataclass


@dataclass
class KafkaRequest:
    bootstrap_servers: str
    group_id: str
    topic: str
    security_protocol: str = ""
    sasl_mechanism: str = ""
    sasl_username: str = ""
    sasl_password: str = ""
    batch_size: int = 1
