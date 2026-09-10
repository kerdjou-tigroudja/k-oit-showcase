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

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SeverityLevel(StrEnum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFO = "INFO"


class ChaosScenarioType(StrEnum):
    DB_POOL_EXHAUSTION = "db_pool_exhaustion"
    OOM_CRASH = "oom_crash"
    UPSTREAM_API_TIMEOUT = "upstream_api_timeout"
    TLS_CERT_EXPIRY = "tls_cert_expiry"
    DISK_FULL = "disk_full"


class TelemetrySignal(BaseModel):
    timestamp: str = Field(..., description="Horodatage du signal au format ISO-8601")
    service: str = Field(..., description="Nom du microservice emetteur")
    signal_type: str = Field(..., description="Type de signal: metric, log ou trace")
    severity: SeverityLevel = Field(
        default=SeverityLevel.INFO, description="Niveau de severite associe"
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Donnees structurees du signal"
    )


class CorrelatedIncident(BaseModel):
    incident_id: str = Field(..., description="Identifiant unique de l incident")
    root_cause_service: str = Field(
        ..., description="Service identifie comme etant la cause racine"
    )
    root_cause_type: str = Field(
        default="", description="Type d incident a l origine de la crise"
    )
    root_cause_signals: list[TelemetrySignal] = Field(
        default_factory=list, description="Signaux lies a la cause racine"
    )
    symptoms: list[str] = Field(
        default_factory=list, description="Liste des symptomes observes"
    )
    signals: list[TelemetrySignal] = Field(
        default_factory=list, description="Ensemble des signaux correles"
    )
    timeline: list[str] = Field(
        default_factory=list, description="Chronologie detaillee des evenements"
    )


class IncidentDiagnosis(BaseModel):
    incident_id: str = Field(..., description="Identifiant unique de l incident")
    severity: SeverityLevel = Field(
        ..., description="Niveau de severite de l incident global"
    )
    root_cause: str = Field(
        ..., description="Description precise de la cause racine isolee"
    )
    impacted_services: list[str] = Field(
        default_factory=list, description="Liste des services impactes"
    )
    timeline: list[str] = Field(
        default_factory=list, description="Chronologie ordonnee de la defaillance"
    )
    recommended_action: str = Field(
        ..., description="Action immediate recommandee pour mitigation"
    )
    verification_command: str = Field(
        ..., description="Commande de verification apres remediation"
    )
    requires_human_approval: bool = Field(
        default=True, description="Indique si une validation humaine est requise"
    )


class MitigationPlan(BaseModel):
    incident_id: str = Field(..., description="Identifiant unique de l incident")
    severity: SeverityLevel = Field(
        default=SeverityLevel.MAJOR, description="Niveau de severite global"
    )
    recommended_actions: list[str] = Field(
        default_factory=list, description="Actions de mitigation recommandees"
    )
    rollback_commands: list[str] = Field(
        default_factory=list, description="Commandes de retour arriere securisees"
    )
    restart_commands: list[str] = Field(
        default_factory=list, description="Commandes de redemarrage securisees"
    )
    verification_script: str = Field(
        default="", description="Script ou commande de validation post-mitigation"
    )
    human_approval_required: bool = Field(
        default=True, description="Approbation humaine strictement obligatoire"
    )


class ChaosScenarioResult(BaseModel):
    scenario_type: ChaosScenarioType = Field(
        ..., description="Type de scenario injecte"
    )
    title: str = Field(..., description="Titre explicite du scenario")
    description: str = Field(
        ..., description="Description detaillee du scenario de chaos"
    )
    expected_root_cause: str = Field(
        ..., description="Cause racine attendue pour ce scenario"
    )
    expected_severity: SeverityLevel = Field(
        ..., description="Niveau de severite attendu"
    )
    signals: list[TelemetrySignal] = Field(
        ..., description="Liste des signaux generes pour la simulation"
    )
