"""Unit tests for CampSeeker agent configuration, client, and tools."""

import os
import pytest
from unittest.mock import patch, MagicMock

from campseeker.config import Settings
from campseeker.client import NPSClient, NPSFailure
from campseeker.tools import (
    search_parks,
    get_campgrounds,
    get_alerts,
    PARK_FIELDS,
    CAMPGROUND_FIELDS,
    ALERT_FIELDS,
)
from campseeker.agent import root_agent


class TestConfig:
    """Test Settings loading and validation."""

    def test_settings_missing_api_key(self, monkeypatch):
        monkeypatch.setenv("NPS_API_KEY", "")
        with pytest.raises(ValueError, match="Set NPS_API_KEY"):
            Settings.from_env()

    def test_settings_invalid_timeout(self, monkeypatch):
        monkeypatch.setenv("NPS_API_KEY", "test-key")
        monkeypatch.setenv("NPS_TIMEOUT_SECONDS", "not-a-number")
        with pytest.raises(ValueError, match="must be a number"):
            Settings.from_env()

    def test_settings_timeout_out_of_range(self, monkeypatch):
        monkeypatch.setenv("NPS_API_KEY", "test-key")
        monkeypatch.setenv("NPS_TIMEOUT_SECONDS", "100")
        with pytest.raises(ValueError, match="between 1 and 60"):
            Settings.from_env()

    def test_settings_valid(self, monkeypatch):
        monkeypatch.setenv("NPS_API_KEY", "valid-nps-key")
        monkeypatch.setenv("NPS_TIMEOUT_SECONDS", "20")
        settings = Settings.from_env()
        assert settings.nps_api_key == "valid-nps-key"
        assert settings.timeout_seconds == 20.0


class TestNPSClient:
    """Test NPSClient parameter validation and mock transport handling."""

    def test_invalid_resource(self):
        client = NPSClient(api_key="test", transport=lambda *args: {})
        res = client.query("unsupported_resource")
        assert res["status"] == "error"
        assert res["error_code"] == "invalid_input"

    def test_limit_and_start_validation(self):
        client = NPSClient(api_key="test", transport=lambda *args: {})
        assert client.query("parks", limit=0)["error_code"] == "invalid_input"
        assert client.query("parks", limit=51)["error_code"] == "invalid_input"
        assert client.query("parks", start=-1)["error_code"] == "invalid_input"

    def test_state_code_validation(self):
        client = NPSClient(api_key="test", transport=lambda *args: {})
        res = client.query("parks", state_code="ZZ")
        assert res["status"] == "error"
        assert "US postal code" in res["message"]

    def test_park_code_validation_for_campgrounds(self):
        client = NPSClient(api_key="test", transport=lambda *args: {})
        # Missing park code
        res = client.query("campgrounds")
        assert res["status"] == "error"
        assert "A park_code is required" in res["message"]

        # Invalid format (must be 4 alphanumeric chars)
        res2 = client.query("campgrounds", park_code="toolongcode")
        assert res2["status"] == "error"
        assert "four-character code" in res2["message"]

    def test_successful_query_with_mock_transport(self):
        mock_data = {
            "total": "1",
            "data": [
                {
                    "id": "123",
                    "parkCode": "acad",
                    "fullName": "Acadia National Park",
                }
            ],
        }

        def mock_transport(resource, params, api_key, timeout):
            assert resource == "parks"
            assert params["stateCode"] == "ME"
            return mock_data

        client = NPSClient(api_key="test", transport=mock_transport)
        res = client.query("parks", state_code="me")

        assert res["status"] == "success"
        assert res["resource"] == "parks"
        assert res["count"] == 1
        assert res["total"] == 1
        assert res["has_more"] is False
        assert len(res["data"]) == 1
        assert res["data"][0]["fullName"] == "Acadia National Park"

    def test_transport_failure_handling(self):
        def failing_transport(resource, params, api_key, timeout):
            raise NPSFailure("rate_limited", "Rate limit reached", retry_after=30)

        client = NPSClient(api_key="test", transport=failing_transport)
        res = client.query("parks", query="Acadia")

        assert res["status"] == "error"
        assert res["error_code"] == "rate_limited"
        assert res["retry_after_seconds"] == 30


class TestTools:
    """Test tool helper functions with mock client queries."""

    @patch("campseeker.tools._client")
    def test_search_parks_field_filtering(self, mock_client_func):
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "status": "success",
            "data": [
                {
                    "id": "1",
                    "parkCode": "acad",
                    "fullName": "Acadia National Park",
                    "unwantedField": "should be stripped",
                }
            ],
        }
        mock_client_func.return_value = mock_client

        res = search_parks(query="Acadia")
        assert res["status"] == "success"
        record = res["data"][0]
        assert "parkCode" in record
        assert "fullName" in record
        assert "unwantedField" not in record

    @patch("campseeker.tools._client")
    def test_get_campgrounds_invocation(self, mock_client_func):
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "status": "success",
            "data": [
                {
                    "id": "c1",
                    "parkCode": "acad",
                    "name": "Blackwoods Campground",
                    "amenities": {"toilets": ["Flush Toilets"]},
                }
            ],
        }
        mock_client_func.return_value = mock_client

        res = get_campgrounds(park_code="acad")
        assert res["status"] == "success"
        assert res["data"][0]["name"] == "Blackwoods Campground"
        mock_client.query.assert_called_once_with(
            "campgrounds",
            park_code="acad",
            limit=20,
            start=0,
        )

    @patch("campseeker.tools._client")
    def test_get_alerts_invocation(self, mock_client_func):
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "status": "success",
            "data": [
                {
                    "id": "a1",
                    "parkCode": "acad",
                    "title": "Park Road Closure",
                    "category": "Park Closure",
                }
            ],
        }
        mock_client_func.return_value = mock_client

        res = get_alerts(park_code="acad")
        assert res["status"] == "success"
        assert res["data"][0]["title"] == "Park Road Closure"


class TestAgentDefinition:
    """Test Root Agent configuration."""

    def test_root_agent_metadata(self):
        assert root_agent.name == "campseeker"
        assert root_agent.tools is not None
        tool_names = [tool.__name__ for tool in root_agent.tools]
        assert "search_parks" in tool_names
        assert "get_campgrounds" in tool_names
        assert "get_alerts" in tool_names

    def test_root_agent_instruction_contains_guardrails(self):
        instruction = root_agent.instruction.lower()
        assert "national park service" in instruction or "nps" in instruction
        assert "search_parks" in instruction
        assert "get_campgrounds" in instruction
        assert "read-only" in instruction or "do not book" in instruction


class TestEvalDatasetAndMetrics:
    """Test evaluation dataset and custom metrics alignment with presentation slides."""

    def test_basic_dataset_cases_align_with_slides(self):
        import json
        from pathlib import Path

        dataset_path = Path(__file__).resolve().parents[1] / "eval" / "datasets" / "basic-dataset.json"
        assert dataset_path.exists()
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        case_ids = {c["eval_case_id"] for c in data["eval_cases"]}
        # Slide 10: One trip-constraint case + four grounding checks
        expected_cases = {
            "trip_constraint_maine_acadia_showers",
            "grounding_amenity_present",
            "grounding_amenity_missing",
            "grounding_no_supported_match",
            "grounding_availability_asked",
        }
        assert expected_cases.issubset(case_ids)

        for case in data["eval_cases"]:
            assert "eval_case_id" in case
            assert "prompt" in case
            assert "reference" in case

    def test_eval_config_metrics(self):
        import yaml
        from pathlib import Path

        config_path = Path(__file__).resolve().parents[1] / "eval" / "eval_config.yaml"
        assert config_path.exists()
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        assert "valid_trip_plan_rate" in cfg["metrics_to_run"]
        assert "custom_response_quality" in cfg["metrics_to_run"]
        assert cfg["thresholds"]["valid_trip_plan_rate"] == 1.0

    @patch("tests.eval.valid_trip_plan_rate._client")
    def test_valid_trip_plan_rate_evaluate(self, mock_client_func):
        from tests.eval.valid_trip_plan_rate import evaluate, _Verdict

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.parsed = _Verdict(score=1, verdict="PASS", explanation="Honors constraints and grounding.")
        mock_client.models.generate_content.return_value = mock_response
        mock_client_func.return_value = mock_client

        res = evaluate({
            "prompt": "Acadia with showers",
            "response": "No campgrounds in Acadia offer verified on-site showers.",
            "reference": "Accurately reports no on-site showers.",
        })
        assert res["score"] == 1
        assert "PASS" in res["explanation"]

