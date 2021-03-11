from typing import List
from dataclasses import dataclass


@dataclass
class LagReportResponseModel:
    topic: str
    group_id: str
    lags: List[int]
    success: bool

    def total_lag(self):
        return sum(self.lags)

    def to_string(self):
        return f"Lag Report: <topic: {self.topic}, group_id: {self.group_id}, lag: {self.total_lag()}>"

    def to_fancy_string(self):
        pass
