"""
tests/test_tools.py
===================
Tests for Module 1 tools and agent construction.
All tests run in mock mode — no GCP credentials required.

Run:
    AGENT_MOCK_GCP=true pytest tests/test_tools.py -v
"""

from __future__ import annotations

import json
import os
import sys

import pytest

os.environ["AGENT_MOCK_GCP"] = "true"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Tool unit tests
# ---------------------------------------------------------------------------

class TestListGcpResources:
    def test_cloud_run_returns_services(self) -> None:
        from module1.tools.gcp_tools import list_gcp_resources
        r = json.loads(list_gcp_resources("cloud_run", "us-central1"))
        assert r["data"]["service_type"] == "cloud_run"
        assert r["data"]["count"] == 4
        assert isinstance(r["data"]["resources"], list)

    def test_compute_returns_instances(self) -> None:
        from module1.tools.gcp_tools import list_gcp_resources
        r = json.loads(list_gcp_resources("compute", "us-central1"))
        assert r["data"]["count"] == 4

    def test_cloud_sql_returns_databases(self) -> None:
        from module1.tools.gcp_tools import list_gcp_resources
        r = json.loads(list_gcp_resources("cloud_sql", "us-central1"))
        assert r["data"]["count"] == 2

    def test_cloud_functions_returns_functions(self) -> None:
        from module1.tools.gcp_tools import list_gcp_resources
        r = json.loads(list_gcp_resources("cloud_functions", "us-central1"))
        assert r["data"]["count"] == 3

    def test_unknown_type_returns_error(self) -> None:
        from module1.tools.gcp_tools import list_gcp_resources
        r = json.loads(list_gcp_resources("unknown", "us-central1"))
        assert "error" in r["data"]

    def test_mock_flag_set(self) -> None:
        from module1.tools.gcp_tools import list_gcp_resources
        r = json.loads(list_gcp_resources("cloud_run", "us-central1"))
        assert r["mock_mode"] is True


class TestDescribeResource:
    def test_known_service_returns_detail(self) -> None:
        from module1.tools.gcp_tools import describe_resource
        r = json.loads(describe_resource("cloud_run", "notification-svc", "us-central1"))
        d = r["data"]
        assert d["name"] == "notification-svc"
        assert "recent_events" in d
        assert len(d["recent_events"]) > 0

    def test_unknown_service_returns_error(self) -> None:
        from module1.tools.gcp_tools import describe_resource
        r = json.loads(describe_resource("cloud_run", "does-not-exist", "us-central1"))
        assert "error" in r["data"]
        assert "hint" in r["data"]


class TestCheckResourceHealth:
    def test_healthy_service(self) -> None:
        from module1.tools.gcp_tools import check_resource_health
        r = json.loads(check_resource_health("cloud_run", "api-gateway-svc", "us-central1"))
        assert r["data"]["health"] == "healthy"
        assert len(r["data"]["findings"]) > 0
        assert r["data"]["recommendations"] == []

    def test_degraded_service(self) -> None:
        from module1.tools.gcp_tools import check_resource_health
        r = json.loads(check_resource_health("cloud_run", "notification-svc", "us-central1"))
        assert r["data"]["health"] == "degraded"
        assert len(r["data"]["recommendations"]) > 0

    def test_no_ha_cloud_sql_is_degraded(self) -> None:
        from module1.tools.gcp_tools import check_resource_health
        r = json.loads(check_resource_health("cloud_sql", "reporting-mysql", "us-central1"))
        assert r["data"]["health"] == "degraded"


class TestGetEnvironmentSummary:
    def test_returns_all_service_types(self) -> None:
        from module1.tools.gcp_tools import get_environment_summary
        r = json.loads(get_environment_summary("us-central1"))
        d = r["data"]
        assert "cloud_run" in d["services"]
        assert "compute" in d["services"]
        assert "cloud_sql" in d["services"]
        assert "cloud_functions" in d["services"]

    def test_overall_health_is_degraded(self) -> None:
        from module1.tools.gcp_tools import get_environment_summary
        r = json.loads(get_environment_summary("us-central1"))
        assert r["data"]["overall_health"] == "degraded"

    def test_action_items_present(self) -> None:
        from module1.tools.gcp_tools import get_environment_summary
        r = json.loads(get_environment_summary("us-central1"))
        assert len(r["data"]["action_items"]) > 0


class TestRequestHumanReview:
    def test_creates_ticket(self, capsys) -> None:
        from module1.tools.gcp_tools import request_human_review
        r = json.loads(request_human_review(
            issue_summary="Test issue",
            urgency="high",
            full_context="context details",
            recommended_action="restart the service",
        ))
        assert r["data"]["status"] == "PENDING_HUMAN_REVIEW"
        assert r["data"]["ticket_id"].startswith("INFRA-")
        assert r["data"]["urgency"] == "HIGH"

    def test_normalises_invalid_urgency(self) -> None:
        from module1.tools.gcp_tools import request_human_review
        r = json.loads(request_human_review(
            issue_summary="x", urgency="INVALID", full_context="x", recommended_action="x"
        ))
        assert r["data"]["urgency"] == "MEDIUM"

    def test_console_output(self, capsys) -> None:
        from module1.tools.gcp_tools import request_human_review
        request_human_review("x", "critical", "ctx", "fix it")
        captured = capsys.readouterr()
        assert "HUMAN REVIEW REQUIRED" in captured.out
        assert "CRITICAL" in captured.out


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

class TestToolRegistry:
    def test_five_tools_registered(self) -> None:
        from module1.tools.gcp_tools import ALL_TOOLS
        assert len(ALL_TOOLS) == 5

    def test_all_tools_have_docstrings(self) -> None:
        from module1.tools.gcp_tools import ALL_TOOLS
        for t in ALL_TOOLS:
            assert t.__doc__ and len(t.__doc__.strip()) > 30, (
                f"Tool {t.__name__} needs a meaningful docstring — "
                "the LLM reads it to understand what the tool does."
            )

    def test_tool_names(self) -> None:
        from module1.tools.gcp_tools import ALL_TOOLS
        names = {t.__name__ for t in ALL_TOOLS}
        assert names == {
            "list_gcp_resources",
            "describe_resource",
            "check_resource_health",
            "get_environment_summary",
            "request_human_review",
        }


# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------

class TestModelConfig:
    def test_vertex_model_returns_id(self) -> None:
        from module1.config.models import get_vertex_model
        model_id = get_vertex_model()
        assert model_id is not None
        assert "gemini" in model_id

    def test_model_garden_returns_endpoint(self) -> None:
        from module1.config.models import get_model_garden_model
        endpoint = get_model_garden_model(
            endpoint_id="projects/my-project/locations/us-central1/endpoints/12345"
        )
        assert endpoint is not None
        assert "endpoints" in endpoint

    def test_provider_info_has_required_keys(self) -> None:
        from module1.config.models import PROVIDER_INFO
        for key, info in PROVIDER_INFO.items():
            for field in ("name", "vendor", "access", "free_trial"):
                assert field in info, f"PROVIDER_INFO['{key}'] missing field '{field}'"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

class TestSystemPrompt:
    @pytest.fixture(autouse=True)
    def _require_adk(self):
        pytest.importorskip("google.adk", reason="google-adk not installed")

    def test_system_prompt_defines_constraints(self) -> None:
        from module1.agent import SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT) > 400
        assert "request_human_review" in SYSTEM_PROMPT

    def test_system_prompt_defines_observation_mode(self) -> None:
        from module1.agent import SYSTEM_PROMPT
        assert "OBSERVE" in SYSTEM_PROMPT or "observe" in SYSTEM_PROMPT.lower()

    def test_system_prompt_defines_tool_usage(self) -> None:
        from module1.agent import SYSTEM_PROMPT
        assert "list_gcp_resources" in SYSTEM_PROMPT
        assert "get_environment_summary" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Agent construction (no LLM calls)
# ---------------------------------------------------------------------------

class TestAgentConstruction:
    def test_create_agent_returns_agent(self) -> None:
        pytest.importorskip("google.adk", reason="google-adk not installed")
        from module1.agent import create_agent
        try:
            agent = create_agent(verbose=False)
            assert agent is not None
        except Exception as exc:
            if any(w in str(exc).lower() for w in ("credential", "auth", "access", "api")):
                pytest.skip(f"GCP credentials not available: {exc}")
            raise


# ---------------------------------------------------------------------------
# Integration tests (require live GCP — skip by default)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS", "").lower() != "true",
    reason="Set RUN_INTEGRATION_TESTS=true and AGENT_MOCK_GCP=false to run",
)
class TestIntegration:
    """
    End-to-end tests against the real ADK agent + Vertex AI.

    Requirements:
        - GCP credentials configured
        - Vertex AI API enabled
        - RUN_INTEGRATION_TESTS=true
        - AGENT_MOCK_GCP=false (or unset)
    """

    @pytest.fixture(scope="class")
    def agent(self):
        os.environ.pop("AGENT_MOCK_GCP", None)
        from module1.agent import create_agent
        return create_agent(verbose=False)

    def test_simple_list_query(self, agent) -> None:
        response = agent("List Cloud Run services in us-central1")
        assert response is not None
        assert len(str(response)) > 10

    def test_health_check_query(self, agent) -> None:
        response = agent("Check the health of notification-svc in us-central1")
        text = str(response).lower()
        assert any(w in text for w in ("health", "running", "instances", "degraded", "critical"))
