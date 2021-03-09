from dataclasses import dataclass, field


@dataclass
class LagResponseModel:
    topic: str
    lags: list = field(default_factory=list)
