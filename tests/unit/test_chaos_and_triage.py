# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from pydantic import ValidationError

from app.chaos_simulator import ChaosSimulator
from app.correlator import IncidentCorrelator
from app.schemas import (
    ChaosScenarioType,
    SeverityLevel,
    TelemetrySignal,
)
from app.tools import (
    correlate_and_diagnose,
    generate_sre_mitigation_plan,
    ingest_opentelemetry_stream,
    list_available_chaos_scenarios,
    run_chaos_scenario,
)


def test_schemas_validation() -> None:
    """Verifie le typage strict des modeles Pydantic."""
    signal = TelemetrySignal(
        timestamp="2026-09-08T08:00:00Z",
        service="test-service",
        signal_type="log",
        severity=SeverityLevel.CRITICAL,
        payload={"message": "System failure"},
    )
    assert signal.service == "test-service"
    assert signal.severity == SeverityLevel.CRITICAL
    assert signal.payload["message"] == "System failure"

    with pytest.raises(ValidationError):
        TelemetrySignal(
            timestamp="invalid",
            service="test-service",
            signal_type="log",
            severity="INVALID_SEVERITY",  # type: ignore
        )


def test_all_five_chaos_scenarios() -> None:
    """Verifie la generation et la completude des 5 scenarios de chaos."""
    scenarios = ChaosSimulator.list_scenarios()
    assert len(scenarios) == 5

    scenario_types = [
        ChaosScenarioType.DB_POOL_EXHAUSTION,
        ChaosScenarioType.OOM_CRASH,
        ChaosScenarioType.UPSTREAM_API_TIMEOUT,
        ChaosScenarioType.TLS_CERT_EXPIRY,
        ChaosScenarioType.DISK_FULL,
    ]

    for st in scenario_types:
        result = ChaosSimulator.generate_scenario(st)
        assert result.scenario_type == st
        assert len(result.title) > 0
        assert len(result.description) > 0
        assert len(result.expected_root_cause) > 0
        assert len(result.signals) >= 3
        for sig in result.signals:
            assert sig.signal_type in ("metric", "log", "trace")
            assert len(sig.service) > 0
            assert sig.timestamp is not None


def test_correlator_causal_isolation() -> None:
    """Verifie l'isolation causale entre cause racine et symptomes collateraux."""
    correlator = IncidentCorrelator()

    # Test Scenario 1: DB Pool Exhaustion
    db_result = ChaosSimulator.generate_scenario(ChaosScenarioType.DB_POOL_EXHAUSTION)
    correlated = correlator.correlate(db_result.signals)
    assert correlated.root_cause_service == "order-service"
    assert correlated.root_cause_type == "db_pool_exhaustion"
    assert len(correlated.root_cause_signals) >= 1
    assert len(correlated.symptoms) >= 1
    assert any("checkout-service" in s for s in correlated.symptoms)

    diagnosis = correlator.diagnose(correlated)
    assert diagnosis.severity == SeverityLevel.CRITICAL
    assert "order-service" in diagnosis.impacted_services
    assert "checkout-service" in diagnosis.impacted_services
    assert diagnosis.requires_human_approval is True
    assert (
        "psql" in diagnosis.verification_command
        or "pg_stat_activity" in diagnosis.verification_command
    )

    # Test Scenario 2: OOM Crash
    oom_result = ChaosSimulator.generate_scenario(ChaosScenarioType.OOM_CRASH)
    correlated_oom = correlator.correlate(oom_result.signals)
    assert correlated_oom.root_cause_service == "recommendation-worker"
    assert correlated_oom.root_cause_type == "oom_crash"
    diagnosis_oom = correlator.diagnose(correlated_oom)
    assert diagnosis_oom.severity == SeverityLevel.CRITICAL
    assert "recommender-api" in diagnosis_oom.impacted_services

    # Test Scenario 3: Upstream Timeout
    upstream_result = ChaosSimulator.generate_scenario(
        ChaosScenarioType.UPSTREAM_API_TIMEOUT
    )
    correlated_upstream = correlator.correlate(upstream_result.signals)
    assert correlated_upstream.root_cause_service == "payment-service"
    assert correlated_upstream.root_cause_type == "upstream_api_timeout"
    diagnosis_upstream = correlator.diagnose(correlated_upstream)
    assert diagnosis_upstream.severity == SeverityLevel.CRITICAL

    # Test Scenario 4: TLS Cert Expiry
    tls_result = ChaosSimulator.generate_scenario(ChaosScenarioType.TLS_CERT_EXPIRY)
    correlated_tls = correlator.correlate(tls_result.signals)
    assert correlated_tls.root_cause_service == "api-ingress"
    assert correlated_tls.root_cause_type == "tls_cert_expiry"
    diagnosis_tls = correlator.diagnose(correlated_tls)
    assert diagnosis_tls.severity == SeverityLevel.CRITICAL
    assert "openssl" in diagnosis_tls.verification_command

    # Test Scenario 5: Disk Full
    disk_result = ChaosSimulator.generate_scenario(ChaosScenarioType.DISK_FULL)
    correlated_disk = correlator.correlate(disk_result.signals)
    assert correlated_disk.root_cause_service == "audit-logging-node"
    assert correlated_disk.root_cause_type == "disk_full"
    diagnosis_disk = correlator.diagnose(correlated_disk)
    assert diagnosis_disk.severity == SeverityLevel.CRITICAL
    assert "df -h" in diagnosis_disk.verification_command


def test_mitigation_plan_human_in_the_loop() -> None:
    """Verifie le respect strict du paradigme Human-in-the-Loop."""
    correlator = IncidentCorrelator()
    db_result = ChaosSimulator.generate_scenario(ChaosScenarioType.DB_POOL_EXHAUSTION)
    correlated = correlator.correlate(db_result.signals)
    diagnosis = correlator.diagnose(correlated)
    plan = correlator.build_mitigation_plan(diagnosis)

    assert plan.human_approval_required is True
    assert len(plan.recommended_actions) >= 3
    assert len(plan.rollback_commands) >= 1
    assert len(plan.restart_commands) >= 1
    assert "Verification terminee" in plan.verification_script


def test_tools_layer() -> None:
    """Verifie l'exposition des outils pour l'agent ADK 2.0."""
    scenarios = list_available_chaos_scenarios()
    assert len(scenarios) == 5

    sim_res = run_chaos_scenario("db_pool_exhaustion")
    assert "signals" in sim_res
    assert len(sim_res["signals"]) > 0

    ingest_res = ingest_opentelemetry_stream(sim_res["signals"])
    assert ingest_res["status"] == "success"
    assert ingest_res["ingested_count"] == len(sim_res["signals"])

    diag_res = correlate_and_diagnose(sim_res["signals"])
    assert diag_res["severity"] == "CRITICAL"
    assert diag_res["requires_human_approval"] is True

    plan_res = generate_sre_mitigation_plan(
        diag_res["incident_id"], scenario_type="db_pool_exhaustion"
    )
    assert plan_res["human_approval_required"] is True
    assert len(plan_res["recommended_actions"]) > 0
