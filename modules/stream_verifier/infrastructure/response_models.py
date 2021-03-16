from typing import List
from dataclasses import dataclass, field


@dataclass
class StreamResponse:
    bootstrap_servers: str
    group_id: str
    topic: str
    lag: int


@dataclass
class LagReportResponseModel:
    streams: List[StreamResponse]
    success: bool
