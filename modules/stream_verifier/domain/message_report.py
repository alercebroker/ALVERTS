from dataclasses import dataclass


@dataclass
class MessageReport:
    topic: str
    n_messages: str
