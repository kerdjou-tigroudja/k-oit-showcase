"""Unit tests for ADK Agent initialization and tools inspection."""

import json
from pathlib import Path

from app.agent import root_agent
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
