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
            {
                "streams": [
                    {
                        "bootstrap_servers": "test",
                        "group_id": "test",
                        "topic": "test",
                    }
                ],
            },
            "lag_report",
        )
        assert len(model.streams) == 1
        assert model.streams[-1].bootstrap_servers == "test"

    def test_detections_report(self, creator):
        model = creator.to_request_model(
            {
                "streams": [
                    {
                        "bootstrap_servers": "test",
                        "group_id": "test",
                        "topic": "test",
                        "identifiers": ["oid", "candid"],
                        "batch_size": "500",
                    }
                ],
                "database": [
                    {
                        "host": "test",
                        "database": "test",
                        "user": "test",
                        "password": "test",
                        "port": "5432",
                        "detections_table_name": "test",
                        "detections_id_field": "test",
                    }
                ],
            },
            "detections_report",
        )
        assert len(model.streams) == 1 and len(model.streams) == len(model.tables)
        assert model.streams[-1].bootstrap_servers == "test"
        assert model.tables[-1].db_url == "postgresql://test:test@test:5432/test"

    def test_stamp_classifications_report(self, creator):
        model = creator.to_request_model(
            {
                "database": [
                    {   
                        "host": "",
                        "database": "",
                        "user": "",
                        "password": "",
                        "port": "",
                        "table_names": "",
                        "mjd_name": ""
                    }
                ],
            },
            "stamp_classifications_report"
        )
        assert len(model.databases) == 1
        assert model.databases[-1].mjd_name == ""
        assert model.databases[-1].table_names == ""
        
