from dataclasses import dataclass
from typing import List,Tuple


@dataclass
class StampClassificationsReport:
    counts: List[Tuple[str, int]]
    observed: int
    new_objects: int
    host: str
    database: str
    def check_success(self):
        return True
