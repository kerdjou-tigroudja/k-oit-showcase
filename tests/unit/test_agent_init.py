"""Unit tests for ADK Agent initialization and tools inspection."""

import json
from pathlib import Path

from app.agent import root_agent


def test_root_agent_initialization():
    """Verify that root SRE agent is correctly instantiated with ADK 2.0."""
    assert root_agent.name == "k_oit"
    assert "sre" in root_agent.instruction.lower() or "incident" in root_agent.instruction.lower()
    assert root_agent.tools is not None
    assert len(root_agent.tools) >= 5


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
