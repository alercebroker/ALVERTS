from dataclasses import dataclass, field


@dataclass
class LagResponseModel:
    topic: str
    group_id: str
    lags: list = field(default_factory=list)
