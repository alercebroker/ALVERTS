from dataclasses import dataclass
from typing import List


@dataclass
class LagReport:
    topic: str
    group_id: str
    lags: List[int]

    def total_lag(self):
        return sum(self.lags)
