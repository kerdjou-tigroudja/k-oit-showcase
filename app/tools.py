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

from typing import Any

from app.chaos_simulator import ChaosSimulator
from app.correlator import IncidentCorrelator
from app.schemas import (
    IncidentDiagnosis,
    SeverityLevel,
    TelemetrySignal,
)

correlator_instance = IncidentCorrelator()


def list_available_chaos_scenarios() -> list[dict[str, str]]:
    """Liste les 5 scenarios de chaos SRE disponibles avec leurs descriptions.

    Returns:
        Une liste de dictionnaires representant chaque scenario disponible.
    """
    return ChaosSimulator.list_scenarios()


def run_chaos_scenario(scenario_type: str) -> dict[str, Any]:
    """Execute le simulateur de chaos pour le scenario specifie et retourne la telemetrie.

    Args:
        scenario_type: Nom du scenario (ex: 'db_pool_exhaustion', 'oom_crash',
            'upstream_api_timeout', 'tls_cert_expiry', 'disk_full').

    Returns:
        Un dictionnaire contenant le scenario, le diagnostic attendu et la telemetrie generee.
    """
    result = ChaosSimulator.generate_scenario(scenario_type)
    return result.model_dump()


def ingest_opentelemetry_stream(signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Valide et ingere un flux de signaux OpenTelemetry (metriques, traces, logs).

    Args:
        signals: Liste de dictionnaires conformes au schema TelemetrySignal.

    Returns:
        Synthese d'ingestion avec le statut, le compte et la liste des erreurs eventuelles.
    """
    validated = []
    errors = []

    for idx, s in enumerate(signals):
        try:
            sig = TelemetrySignal(**s)
            validated.append(sig.model_dump())
        except Exception as e:
            errors.append(f"Signal index {idx} invalide: {e!s}")

    return {
        "status": "success" if not errors else "partial_success",
        "total_received": len(signals),
        "ingested_count": len(validated),
        "signals": validated,
        "errors": errors,
    }


def correlate_and_diagnose(signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Execute la correlation causale complete, isole la cause racine et formule le diagnostic.

    Args:
        signals: Liste de signaux d'observabilite (dictionnaires).

    Returns:
        Rapport d'incident complet contenant la cause racine, les symptomes et la chronologie.
    """
    telemetry_signals: list[TelemetrySignal] = []
    for s in signals:
        try:
            telemetry_signals.append(TelemetrySignal(**s))
        except Exception:
            pass

    correlated = correlator_instance.correlate(telemetry_signals)
    diagnosis = correlator_instance.diagnose(correlated)
    return diagnosis.model_dump()


def generate_sre_mitigation_plan(
    incident_id: str, scenario_type: str = ""
) -> dict[str, Any]:
    """Produit un plan de mitigation SRE securise avec contrainte Human-in-the-Loop stricte.

    Args:
        incident_id: Identifiant unique de l'incident a traiter.
        scenario_type: Type de scenario optionnel pour orienter le plan de secours.

    Returns:
        Plan de mitigation structure avec actions recommandees, rollback et redemarrage.
    """
    if scenario_type:
        result = ChaosSimulator.generate_scenario(scenario_type)
        correlated = correlator_instance.correlate(result.signals)
        diagnosis = correlator_instance.diagnose(correlated)
    else:
        diagnosis = IncidentDiagnosis(
            incident_id=incident_id,
            severity=SeverityLevel.MAJOR,
            root_cause="Defaillance operationnelle non specifiee necessitant investigation.",
            impacted_services=["core-application"],
            timeline=[],
            recommended_action="Inspecter les métriques et journaux applicatifs.",
            verification_command="kubectl get pods -n production",
            requires_human_approval=True,
        )

    plan = correlator_instance.build_mitigation_plan(diagnosis)
    plan.human_approval_required = True
    return plan.model_dump()
