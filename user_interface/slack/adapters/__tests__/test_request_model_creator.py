import pytest
from user_interface.slack.adapters.slack_request_model_creator import (
    SlackRequestModelCreator,
)


class TestToRequestModel:
    @pytest.fixture
    def creator(self):
        return SlackRequestModelCreator()

    def test_lag_report(self, creator):
        model = creator.to_request_model(
            [
                {
                    "bootstrap_servers": "test",
                    "group_id": "test",
                    "topic": "test",
                }
            ],
            "lag_report",
        )
        assert len(model.streams) == 1
        assert model.streams[-1].bootstrap_servers == "test"
