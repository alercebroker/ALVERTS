from dataclasses import dataclass


@dataclass
class StreamRequestModel:
    bootstrap_servers: str
    group_id: str
    topic: str
