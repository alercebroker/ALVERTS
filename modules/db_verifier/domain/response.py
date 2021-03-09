from dataclasses import dataclass

@dataclass
class DBVerifierResponse:
    """Class for keeping track of an item in inventory."""
    missing: list
    processed: int = 0
    difference: int = 0
    total: int = 0