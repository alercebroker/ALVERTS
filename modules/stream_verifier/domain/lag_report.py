from dataclasses import dataclass
from typing import List


@dataclass
class LagReport:
    bootstrap_servers: str
    topic: str
    group_id: str
    lags: List[int]

    def total_lag(self):
        return sum(self.lags)

    def check_success(self):
        return self.total_lag() == 0
