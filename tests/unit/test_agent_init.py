"""Unit tests for ADK Agent initialization and tools inspection."""

import ast
import json
from pathlib import Path

import app.agent as agent
from app.agent import ensure_analytics_dataset, root_agent
from app.tools import (
    correlate_and_diagnose,
    generate_sre_mitigation_plan,
    ingest_opentelemetry_stream,
    list_available_chaos_scenarios,
    run_chaos_scenario,
)


def test_root_agent_initialization():
    """Verify that root SRE agent is correctly instantiated with ADK 2.0."""
    assert root_agent.name == "k_oit"
    assert "sre" in root_agent.instruction.lower() or "incident" in root_agent.instruction.lower()
    assert root_agent.tools is not None
    assert len(root_agent.tools) >= 5


def test_tools_functional_interfaces():
    """Verify that all tools can be called directly and return expected structures."""
    scenarios = list_available_chaos_scenarios()
    assert len(scenarios) == 5

    sim_res = run_chaos_scenario("db_pool_exhaustion")
    assert sim_res["scenario_type"] == "db_pool_exhaustion"
    assert "order-service" in sim_res["expected_root_cause"]

    ingest_res = ingest_opentelemetry_stream(sim_res["signals"])
    assert ingest_res["status"] == "success"
    assert ingest_res["ingested_count"] == len(sim_res["signals"])

    diagnosis = correlate_and_diagnose(sim_res["signals"])
    assert diagnosis["severity"] == "CRITICAL"
    assert diagnosis["requires_human_approval"] is True

    plan = generate_sre_mitigation_plan(diagnosis["incident_id"], scenario_type="db_pool_exhaustion")
    assert plan["human_approval_required"] is True
    assert len(plan["recommended_actions"]) > 0
    assert len(plan["rollback_commands"]) > 0


def test_agent_card_validity():
    """Verify that docs/agent-card.json is schema compliant with A2A protocol."""
    card_path = Path("docs/agent-card.json")
    assert card_path.exists()

    with open(card_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["name"] == "k_oit"
    assert "europe-west9" in data["runtime"]["region"]
    assert len(data["skills"]) >= 5
    assert data["evaluation_metrics"]["root_cause_accuracy"] == "100.0%"


def _module_level_calls(source: str, name: str) -> list[int]:
    """Line numbers of calls to ``name`` outside function and class bodies."""
    tree = ast.parse(source)
    found: list[int] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            called = None
            if isinstance(func, ast.Name):
                called = func.id
            elif isinstance(func, ast.Attribute):
                called = func.attr
            if called == name:
                found.append(child.lineno)
    return found


def test_lifespan_creates_analytics_dataset():
    """The serving process creates the dataset during startup, not import."""
    source = Path("app/fast_api_app.py").read_text(encoding="utf-8")
    assert "ensure_analytics_dataset()" in source


def test_create_dataset_is_not_called_at_import():
    """Importing the agent must not create a BigQuery dataset."""
    source = Path("app/agent.py").read_text(encoding="utf-8")
    assert _module_level_calls(source, "create_dataset") == []
    assert _module_level_calls(source, "ensure_analytics_dataset") == []
    tree = ast.parse(source)
    functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    assert "ensure_analytics_dataset" in functions


def test_ensure_analytics_dataset_creates_dataset(monkeypatch):
    """Startup helper creates the configured dataset and tolerates an existing one."""
    created: dict[str, object] = {}

    class FakeClient:
        def __init__(self, project: str) -> None:
            created["project"] = project

        def create_dataset(self, dataset_ref: str, exists_ok: bool = False) -> None:
            created["ref"] = dataset_ref
            created["exists_ok"] = exists_ok

    monkeypatch.setattr(agent, "_project_id", "demo-project")
    monkeypatch.setattr(agent, "_dataset_id", "adk_agent_analytics")
    monkeypatch.setattr(agent.bigquery, "Client", FakeClient)

    ensure_analytics_dataset()

    assert created == {
        "project": "demo-project",
        "ref": "demo-project.adk_agent_analytics",
        "exists_ok": True,
    }


def test_ensure_analytics_dataset_skips_without_project(monkeypatch):
    """No project id means no BigQuery client."""
    monkeypatch.setattr(agent, "_project_id", None)

    class FakeClient:
        def __init__(self, project: str) -> None:
            raise AssertionError(project)

    monkeypatch.setattr(agent.bigquery, "Client", FakeClient)
    ensure_analytics_dataset()


def test_env_example_omits_unread_a2a_remote_url():
    """A2A_REMOTE_URL is not read by the app, so the example must not advertise it."""
    example = Path(".env.example").read_text(encoding="utf-8")
    assert "A2A_REMOTE_URL" not in example
    assert "BQ_ANALYTICS_DATASET_ID" in example


def test_services_comment_does_not_claim_agent_pins_global():
    """agent.py reads GOOGLE_CLOUD_LOCATION; it does not pin that value to global."""
    source = Path("app/app_utils/services.py").read_text(encoding="utf-8")
    assert 'pins to "global"' not in source
    assert "Cloud Run sets that to \"global\"" in source
