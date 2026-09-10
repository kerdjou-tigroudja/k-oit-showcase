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

import json
import uuid

from app.schemas import (
    CorrelatedIncident,
    IncidentDiagnosis,
    MitigationPlan,
    SeverityLevel,
    TelemetrySignal,
)


class IncidentCorrelator:
    """Moteur de correlation causale pour le triage des incidents SRE K-OIT.

    Analyse les signaux d'observabilite distribues (metriques, traces, logs)
    pour identifier la cause racine et distinguer les symptomes collateraux.
    """

    def correlate(self, signals: list[TelemetrySignal]) -> CorrelatedIncident:
        """Analyse topologique et temporelle des signaux OTel pour isoler la cause racine.

        Args:
            signals: Liste des signaux de telemetrie a correler.

        Returns:
            CorrelatedIncident contenant l'isolation cause racine vs symptomes collateraux.
        """
        if not signals:
            return CorrelatedIncident(
                incident_id=str(uuid.uuid4())[:8],
                root_cause_service="unknown",
                root_cause_type="indetermine",
                root_cause_signals=[],
                symptoms=[],
                signals=[],
                timeline=[],
            )

        sorted_signals = sorted(signals, key=lambda s: s.timestamp)

        root_cause_service = "unknown"
        root_cause_type = "general_incident"
        root_cause_signals: list[TelemetrySignal] = []
        symptoms: list[str] = []
        timeline: list[str] = []

        for sig in sorted_signals:
            payload_str = json.dumps(sig.payload, ensure_ascii=False)
            timeline.append(
                f"[{sig.timestamp}] Service: {sig.service} | Type: {sig.signal_type.upper()} | "
                f"Severity: {sig.severity.value} | Details: {payload_str}"
            )

            is_root_indicator = False
            p = sig.payload
            msg = (
                str(p.get("message", "")).lower()
                + " "
                + str(p.get("error_message", "")).lower()
            )
            metric_name = str(p.get("metric_name", "")).lower()
            val = p.get("value", 0)

            # Verification des patterns de cause racine premiere
            if (
                "fatal" in msg
                or "remaining connection slots" in msg
                or ("connections_active" in metric_name and val >= 100)
            ):
                is_root_indicator = True
                detected_type = "db_pool_exhaustion"
            elif (
                "out of memory" in msg
                or "oom" in msg
                or ("container_memory" in metric_name and val >= 1900000000)
            ):
                is_root_indicator = True
                detected_type = "oom_crash"
            elif "certificate has expired" in msg or (
                "ssl_certificate" in metric_name and val <= 0
            ):
                is_root_indicator = True
                detected_type = "tls_cert_expiry"
            elif "no space left on device" in msg or (
                "disk_utilization" in metric_name and val >= 99
            ):
                is_root_indicator = True
                detected_type = "disk_full"
            elif "read operation timed out" in msg or (
                "dependency_latency" in metric_name and val >= 10000
            ):
                is_root_indicator = True
                detected_type = "upstream_api_timeout"
            else:
                detected_type = "collateral_anomaly"

            if is_root_indicator:
                if root_cause_service == "unknown":
                    root_cause_service = sig.service
                    root_cause_type = detected_type
                    root_cause_signals.append(sig)
                elif sig.service == root_cause_service:
                    root_cause_signals.append(sig)
                else:
                    symptoms.append(
                        f"{sig.service}: {sig.signal_type} anomaly ({msg[:80]})"
                    )
            elif sig.severity in (SeverityLevel.CRITICAL, SeverityLevel.MAJOR):
                symptoms.append(
                    f"{sig.service}: {sig.signal_type} status {p.get('http_status', 'error')} ({msg[:80]})"
                )

        # Fallback si aucun pattern explicite trouve
        if root_cause_service == "unknown":
            root_cause_service = sorted_signals[0].service
            root_cause_signals.append(sorted_signals[0])

        return CorrelatedIncident(
            incident_id=str(uuid.uuid4())[:8],
            root_cause_service=root_cause_service,
            root_cause_type=root_cause_type,
            root_cause_signals=root_cause_signals,
            symptoms=symptoms,
            signals=sorted_signals,
            timeline=timeline,
        )

    def diagnose(self, correlated: CorrelatedIncident) -> IncidentDiagnosis:
        """Formule le diagnostic complet et structure de l'incident.

        Args:
            correlated: Incident prealablement correle par l'IncidentCorrelator.

        Returns:
            IncidentDiagnosis avec cause racine, severite et recommandation.
        """
        root_service = correlated.root_cause_service
        root_type = correlated.root_cause_type
        incident_id = correlated.incident_id

        impacted_services: set[str] = {root_service}
        for sig in correlated.signals:
            impacted_services.add(sig.service)

        severity = SeverityLevel.CRITICAL

        if root_type == "db_pool_exhaustion":
            root_cause = (
                f"Saturation complete du pool de connexions de base de donnees sur {root_service} "
                "(connexions actives 100/100). Impossibilite d'acquerir de nouvelles connexions "
                "entrainant des erreurs 500 et des timeouts 504 en cascade sur les appelants."
            )
            recommended_action = (
                "Augmenter temporairement la taille maximale du pool (max_connections), purger "
                "les connexions orphelines (idle connections) et redemarrer le pool de connexion."
            )
            verification_command = f"kubectl exec -it deploy/{root_service} -- psql -c 'SELECT count(*) FROM pg_stat_activity;'"

        elif root_type == "oom_crash":
            root_cause = (
                f"Fuite memoire progressive sur {root_service} ayant declenche le Linux Kernel "
                "OOM Killer (signal 137). Le conteneur a ete brusquement arrete, rompant "
                "les communications RPC et generant des erreurs 503."
            )
            recommended_action = (
                "Augmenter temporairement la limite de memoire Kubernetes (resources.limits.memory), "
                "isoler le dump memoire pour audit du code applicatif, et redemarrer le deploiement."
            )
            verification_command = f"kubectl get pods -l app={root_service} -o jsonpath='{{range .items[*]}}{{.status.containerStatuses[*].lastState.terminated.reason}}{{\"\\n\"}}{{end}}'"

        elif root_type == "upstream_api_timeout":
            root_cause = (
                f"Degradation critique de latence (>30s) d'une dependance externe via {root_service}. "
                "Depassement du delai de garde entrainant l'epuisement des threads applicatifs "
                "et des timeouts 504 Gateway Timeout propages vers l'amont."
            )
            recommended_action = (
                "Enclencher le disjoncteur (Circuit Breaker) pour court-circuiter l'appel defaillant, "
                "basculer vers un mode degrade ou un endpoint de secours, et notifier le partenaire."
            )
            verification_command = (
                "curl -Iv -m 5 https://api.payment-partner-gateway.com/healthz"
            )

        elif root_type == "tls_cert_expiry":
            root_cause = (
                f"Expiration du certificat SSL/TLS sur {root_service}. Echec systematique de la "
                "negociation TLS (CERTIFICATE_VERIFY_FAILED) bloquant l'integrite du trafic entrant."
            )
            recommended_action = (
                "Renouveler d'urgence le certificat TLS via Cert-Manager / Secret Kubernetes "
                "et forcer le rechargement de la passerelle d'ingress."
            )
            verification_command = f"openssl s_client -connect {root_service}:443 -servername {root_service} < /dev/null 2>/dev/null | openssl x509 -noout -dates"

        elif root_type == "disk_full":
            root_cause = (
                f"Saturation a 100% de l'espace disque sur {root_service} (/var/log). Exception "
                "systeme OSError [Errno 28] No space left on device empechant l'ecriture "
                "des journaux d'audit et bloquant le processus principal."
            )
            recommended_action = (
                "Executer la purge immediate des fichiers de logs archives (.gz), compresser les "
                "journaux anciens et ajuster la politique de retention logrotate."
            )
            verification_command = (
                f"kubectl exec -it deploy/{root_service} -- df -h /var/log"
            )

        else:
            root_cause = f"Defaillance operationnelle detectee sur {root_service} avec propagation multi-services."
            recommended_action = "Inspecter les logs detailles du service et verifier les metriques de sante."
            verification_command = f"kubectl logs deploy/{root_service} --tail=100"
            severity = SeverityLevel.MAJOR

        return IncidentDiagnosis(
            incident_id=incident_id,
            severity=severity,
            root_cause=root_cause,
            impacted_services=sorted(impacted_services),
            timeline=correlated.timeline,
            recommended_action=recommended_action,
            verification_command=verification_command,
            requires_human_approval=True,
        )

    def build_mitigation_plan(self, diagnosis: IncidentDiagnosis) -> MitigationPlan:
        """Elabore un plan de mitigation SRE Human-in-the-Loop strict.

        Args:
            diagnosis: Diagnostic prealable formule par le diagnostician.

        Returns:
            MitigationPlan avec actions recommandees, commandes de rollback et redemarrage.
        """
        root_service = (
            diagnosis.impacted_services[0]
            if diagnosis.impacted_services
            else "application"
        )

        recommended_actions = [
            f"1. Emettre une alerte de crise SRE avec la severite {diagnosis.severity.value}.",
            f"2. {diagnosis.recommended_action}",
            f"3. Verifier le retablissement du service via : {diagnosis.verification_command}",
            "4. Maintenir une surveillance active des metriques pendant 15 minutes post-mitigation.",
        ]

        rollback_commands = [
            f"kubectl rollout undo deployment/{root_service} -n production",
            "kubectl get pods -n production -w",
        ]

        restart_commands = [
            f"kubectl rollout restart deployment/{root_service} -n production",
            f"kubectl rollout status deployment/{root_service} -n production",
        ]

        verification_script = (
            f"#!/usr/bin/env bash\n"
            f"set -euo pipefail\n"
            f"echo 'Verification post-incident {diagnosis.incident_id}...'\n"
            f"{diagnosis.verification_command}\n"
            f"echo 'Verification terminee avec succes.'\n"
        )

        return MitigationPlan(
            incident_id=diagnosis.incident_id,
            severity=diagnosis.severity,
            recommended_actions=recommended_actions,
            rollback_commands=rollback_commands,
            restart_commands=restart_commands,
            verification_script=verification_script,
            human_approval_required=True,
        )
