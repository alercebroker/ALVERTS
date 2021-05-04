from typing import List, Tuple
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


@dataclass
class DifferenceResponse:
    bootstrap_servers: str
    group_id: str
    topic: str
    difference: List
    total_messages: int
    processed: int


@dataclass
class DetectionsReportResponseModel:
    streams: List[DifferenceResponse]
    success: bool

@dataclass
class StampDatabaseResponse:
    counts: List[Tuple[str, int]]
    host: str
    database: str

@dataclass
class StampClassificationsReportResponseModel:
    databases: List[StampDatabaseResponse]
    success: bool