from dataclasses import dataclass, field
from typing import Any


@dataclass
class KafkaResponse:
    topic: str
    group_id: str
    data: Any
