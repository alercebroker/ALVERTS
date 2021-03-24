from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class DetectionsReport:
    bootstrap_servers: str
    topic: str
    group_id: str
    difference: List[Tuple[str, int]]
    total_alerts: int

    def check_success(self):
        return len(self.difference) == 0

    def processed_alerts(self):
        return self.total_alerts - len(self.difference)
