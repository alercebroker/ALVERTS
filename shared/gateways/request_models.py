from dataclasses import dataclass
from typing import List


@dataclass
class KafkaRequest:
    bootstrap_servers: str
    group_id: str
    topic: str
    batch_size: int = 1
