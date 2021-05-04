from dataclasses import dataclass
from typing import List,Tuple


@dataclass
class StampClassificationsReport:
    counts: List[Tuple[str, int]]

    def check_success(self):
        return True
