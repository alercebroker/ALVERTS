import pytest
import verifier
from sqlalchemy.exc import ArgumentError


class TestDBVerifier:
    def test_engine_creation_error(self):
        db_connection = "test"
        with pytest.raises(ArgumentError):
            verifier.DBVerifier(["test"], "localhost:9092", "detection", db_connection)
