from dataclasses import dataclass, field


@dataclass
class StreamRequestModel:
    bootstrap_servers: str
    group_id: str
    topic: str


@dataclass
class LagResponseModel:
    topic: str
    lags: list = field(default_factory=list)
