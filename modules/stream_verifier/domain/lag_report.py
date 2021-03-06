from dataclasses import dataclass


@dataclass
class LagReport:
    topic: str
    lags: int

    def total_lag(self):
        return sum(self.lags)
