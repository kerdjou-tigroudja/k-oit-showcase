# app/chaos_simulator.py
# Simulateur de chaos SRE pour K-OIT.
# Fins de lignes Unix LF strictes, encodage UTF-8 sans BOM.
# Zero emoji dans le code et les commentaires.

from datetime import UTC, datetime, timedelta

from app.schemas import (
    ChaosScenarioResult,
    ChaosScenarioType,
    SeverityLevel,
    TelemetrySignal,
)


class ChaosSimulator:
    """Simulateur de scenarios de chaos SRE pour valider les capacites d analyse de K-OIT."""

    @classmethod
    def list_scenarios(cls) -> list[dict[str, str]]:
        """Retourne la liste des scenarios de chaos disponibles avec leurs descriptions."""
        return [
            {
                "type": ChaosScenarioType.DB_POOL_EXHAUSTION.value,
                "title": "Epuisement du pool de connexions de la base de donnees",
                "description": (
                    "Saturation complete du pool de connexions PostgreSQL (100/100) par le service "
                    "order-service, entrainant des erreurs de connexion fatales en cascade et "
                    "un timeout 504 sur le service checkout-service."
                ),
            },
            {
                "type": ChaosScenarioType.OOM_CRASH.value,
                "title": "Crash par manque de memoire (Out Of Memory)",
                "description": (
                    "Fuite memoire lente sur recommendation-worker provoquant une saturation de "
                    "la RAM (99.8%) suivie d un kill du processus par le noyau Linux (OOM-killer), "
                    "entrainant des erreurs HTTP 503 en cascade sur recommender-api."
                ),
            },
            {
                "type": ChaosScenarioType.UPSTREAM_API_TIMEOUT.value,
                "title": "Timeout d une API partenaire externe",
                "description": (
                    "La latence de l API externe payment-partner-gateway passe brusquement de "
                    "80ms a 30000ms (30s), provoquant des erreurs httpx.ReadTimeout et des "
                    "erreurs 504 Gateway Timeout en cascade sur payment-service."
                ),
            },
            {
                "type": ChaosScenarioType.TLS_CERT_EXPIRY.value,
                "title": "Expiration de certificat TLS/SSL sur l ingress API",
                "description": (
                    "Expiration du certificat SSL de l api-ingress bloquant tous les handshakes "
                    "avec des erreurs ssl.SSLCertVerificationError, provoquant une interruption "
                    "totale des flux entrants."
                ),
            },
            {
                "type": ChaosScenarioType.DISK_FULL.value,
                "title": "Saturation du disque dur (Espace disque plein)",
                "description": (
                    "Saturation a 100% de la partition /var/log sur audit-logging-node bloquant "
                    "les ecritures avec des erreurs OSError [Errno 28] No space left on device, "
                    "verrouillant le service d audit de securite."
                ),
            },
        ]

    @classmethod
    def generate_scenario(
        cls, scenario_type: ChaosScenarioType | str
    ) -> ChaosScenarioResult:
        """Genere un resultat de scenario de chaos SRE simule avec sa telemetrie de crise associee.

        Args:
            scenario_type: Le type de scenario de chaos a generer (ChaosScenarioType ou chaine).

        Returns:
            ChaosScenarioResult contenant le diagnostic de depart et la liste des signaux de telemetrie.
        """
        if isinstance(scenario_type, str):
            try:
                scenario_type = ChaosScenarioType(scenario_type)
            except ValueError as err:
                raise ValueError(
                    f"Type de scenario de chaos inconnu: {scenario_type}"
                ) from err

        now = datetime.now(UTC)

        if scenario_type == ChaosScenarioType.DB_POOL_EXHAUSTION:
            return cls._generate_db_pool_exhaustion(now)
        elif scenario_type == ChaosScenarioType.OOM_CRASH:
            return cls._generate_oom_crash(now)
        elif scenario_type == ChaosScenarioType.UPSTREAM_API_TIMEOUT:
            return cls._generate_upstream_api_timeout(now)
        elif scenario_type == ChaosScenarioType.TLS_CERT_EXPIRY:
            return cls._generate_tls_cert_expiry(now)
        elif scenario_type == ChaosScenarioType.DISK_FULL:
            return cls._generate_disk_full(now)
        else:
            raise ValueError(f"Type de scenario non supporte: {scenario_type}")

    @classmethod
    def _generate_db_pool_exhaustion(cls, base_time: datetime) -> ChaosScenarioResult:
        """Simule la saturation du pool de connexions PostgreSQL."""
        signals = []

        # T-4m : Hausse anormale du nombre de connexions actives
        t_minus_4 = (base_time - timedelta(minutes=4)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_4,
                service="order-service",
                signal_type="metric",
                severity=SeverityLevel.MINOR,
                payload={
                    "metric_name": "db_connections_active",
                    "value": 85.0,
                    "max_limit": 100.0,
                    "database": "orders_db",
                },
            )
        )

        # T-3m : Saturation a 100/100
        t_minus_3 = (base_time - timedelta(minutes=3)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_3,
                service="order-service",
                signal_type="metric",
                severity=SeverityLevel.MAJOR,
                payload={
                    "metric_name": "db_connections_active",
                    "value": 100.0,
                    "max_limit": 100.0,
                    "database": "orders_db",
                },
            )
        )

        # T-2m30s : Premiere erreur fatale dans les logs PostgreSQL d order-service
        t_minus_2_30 = (base_time - timedelta(minutes=2, seconds=30)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_2_30,
                service="order-service",
                signal_type="log",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "logger": "django.db.backends",
                    "message": "FATAL: remaining connection slots are reserved for non-replication superuser connections",
                    "error_class": "OperationalError",
                },
            )
        )

        # T-2m : cascade d erreurs HTTP 500 sur order-service
        t_minus_2 = (base_time - timedelta(minutes=2)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_2,
                service="order-service",
                signal_type="trace",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "trace_id": "9f257a0bc8e1467ba9e1c3b4a243d6c7",
                    "span_id": "b3e94a8c9e01",
                    "http_method": "POST",
                    "http_path": "/api/v1/orders",
                    "http_status": 500,
                    "duration_ms": 15200.0,
                    "error_message": "Could not acquire database connection from pool after 15000ms",
                },
            )
        )

        # T-1m : Erreur 504 Gateway Timeout sur checkout-service qui appelle order-service
        t_minus_1 = (base_time - timedelta(minutes=1)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_1,
                service="checkout-service",
                signal_type="trace",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "trace_id": "9f257a0bc8e1467ba9e1c3b4a243d6c7",
                    "span_id": "c1a89b7cde22",
                    "http_method": "POST",
                    "http_path": "/api/v1/checkout",
                    "http_status": 504,
                    "duration_ms": 30120.0,
                    "upstream_service": "order-service",
                    "error_message": "Upstream service timeout or bad gateway during order creation",
                },
            )
        )

        return ChaosScenarioResult(
            scenario_type=ChaosScenarioType.DB_POOL_EXHAUSTION,
            title="Saturating Database Connection Pool",
            description=(
                "Simulation d un epuisement total du pool de connexions de la base orders_db "
                "provoque par order-service, creant des erreurs FATAL de slots de connexions "
                "et des timeouts 504 en cascade sur le service amont checkout-service."
            ),
            expected_root_cause="orders_db connection pool saturation (100/100) on order-service",
            expected_severity=SeverityLevel.CRITICAL,
            signals=signals,
        )

    @classmethod
    def _generate_oom_crash(cls, base_time: datetime) -> ChaosScenarioResult:
        """Simule un crash OOM sur recommendation-worker et ses impacts."""
        signals = []

        # T-5m : Hausse progressive de l usage RAM
        t_minus_5 = (base_time - timedelta(minutes=5)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_5,
                service="recommendation-worker",
                signal_type="metric",
                severity=SeverityLevel.MINOR,
                payload={
                    "metric_name": "container_memory_usage_bytes",
                    "value": 1820000000.0,
                    "max_limit": 2000000000.0,
                    "memory_utilization_pct": 91.0,
                },
            )
        )

        # T-3m : RAM critique a 99.8%
        t_minus_3 = (base_time - timedelta(minutes=3)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_3,
                service="recommendation-worker",
                signal_type="metric",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "metric_name": "container_memory_usage_bytes",
                    "value": 1996000000.0,
                    "max_limit": 2000000000.0,
                    "memory_utilization_pct": 99.8,
                },
            )
        )

        # T-2m : Log d erreur kernel Out of memory (Killed process)
        t_minus_2 = (base_time - timedelta(minutes=2)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_2,
                service="recommendation-worker",
                signal_type="log",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "kernel_system": "dmesg",
                    "message": "Out of memory: Killed process 4122 (python3) total-vm:4231120kB, anon-rss:1995800kB, file-rss:0kB, shmem-rss:0kB, uid:1000 pgtables:8240kB oom_score_adj:0",
                    "exit_code": 137,
                },
            )
        )

        # T-1m : recommender-api n arrive plus a joindre le worker
        t_minus_1 = (base_time - timedelta(minutes=1)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_1,
                service="recommender-api",
                signal_type="trace",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "trace_id": "a82c6109e2cf4b91b8a531f82c4033f2",
                    "span_id": "d0e12a0349bc",
                    "http_method": "GET",
                    "http_path": "/api/v1/recommendations/user/782",
                    "http_status": 503,
                    "duration_ms": 120.0,
                    "error_message": "gRPC Error: connection refused to recommendation-worker:50051",
                },
            )
        )

        return ChaosScenarioResult(
            scenario_type=ChaosScenarioType.OOM_CRASH,
            title="Out Of Memory (OOM) Crash on Worker",
            description=(
                "Simulation d une fuite memoire critique sur recommendation-worker menant "
                "a un arret brutal par le noyau Linux (OOM-killer, signal 137), cassant "
                "les appels gRPC de recommender-api qui retourne des erreurs HTTP 503."
            ),
            expected_root_cause="Memory leak on recommendation-worker leading to kernel OOM-kill",
            expected_severity=SeverityLevel.CRITICAL,
            signals=signals,
        )

    @classmethod
    def _generate_upstream_api_timeout(cls, base_time: datetime) -> ChaosScenarioResult:
        """Simule une degradation de latence et timeout sur une API partenaire externe."""
        signals = []

        # T-5m : Latence normale
        t_minus_5 = (base_time - timedelta(minutes=5)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_5,
                service="payment-service",
                signal_type="metric",
                severity=SeverityLevel.INFO,
                payload={
                    "metric_name": "external_dependency_latency_ms",
                    "dependency": "payment-partner-gateway",
                    "value": 82.0,
                },
            )
        )

        # T-3m : Latence qui explose (30000ms)
        t_minus_3 = (base_time - timedelta(minutes=3)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_3,
                service="payment-service",
                signal_type="metric",
                severity=SeverityLevel.MAJOR,
                payload={
                    "metric_name": "external_dependency_latency_ms",
                    "dependency": "payment-partner-gateway",
                    "value": 30000.0,
                },
            )
        )

        # T-2m : Log d erreur httpx.ReadTimeout sur payment-service
        t_minus_2 = (base_time - timedelta(minutes=2)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_2,
                service="payment-service",
                signal_type="log",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "logger": "httpx",
                    "message": "httpx.ReadTimeout: The read operation timed out after 30.0 seconds.",
                    "target_url": "https://api.payment-partner-gateway.com/v2/charges",
                },
            )
        )

        # T-1m : Erreur HTTP 504 Gateway Timeout en cascade sur payment-service
        t_minus_1 = (base_time - timedelta(minutes=1)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_1,
                service="payment-service",
                signal_type="trace",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "trace_id": "41a12e09b83f47e2a912e73bc110dfab",
                    "span_id": "f03a11b8ca04",
                    "http_method": "POST",
                    "http_path": "/api/v1/payments/process",
                    "http_status": 504,
                    "duration_ms": 30050.0,
                    "error_message": "Gateway Timeout: Upstream partner gateway timed out",
                },
            )
        )

        return ChaosScenarioResult(
            scenario_type=ChaosScenarioType.UPSTREAM_API_TIMEOUT,
            title="External Upstream API Latency Timeout",
            description=(
                "Simulation d une extreme degradation de latence sur l API externe "
                "payment-partner-gateway (80ms -> 30s), provoquant des exceptions "
                "httpx.ReadTimeout et des erreurs HTTP 504 en cascade sur payment-service."
            ),
            expected_root_cause="Extreme response delay (30s) on external gateway payment-partner-gateway.com",
            expected_severity=SeverityLevel.CRITICAL,
            signals=signals,
        )

    @classmethod
    def _generate_tls_cert_expiry(cls, base_time: datetime) -> ChaosScenarioResult:
        """Simule l expiration d un certificat TLS/SSL sur l api-ingress."""
        signals = []

        # T-3m : Alerte de certificat SSL expire detectee
        t_minus_3 = (base_time - timedelta(minutes=3)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_3,
                service="api-ingress",
                signal_type="metric",
                severity=SeverityLevel.MAJOR,
                payload={
                    "metric_name": "ssl_certificate_days_to_expiry",
                    "domain": "api.k-oit.internal",
                    "value": -1.0,
                },
            )
        )

        # T-2m : Log d erreur de handshake SSL cote ingress
        t_minus_2 = (base_time - timedelta(minutes=2)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_2,
                service="api-ingress",
                signal_type="log",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "logger": "nginx.ingress",
                    "message": "ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate has expired (_ssl.c:1129)",
                    "client_ip": "192.168.42.15",
                    "server_name": "api.k-oit.internal",
                },
            )
        )

        # T-1m : Coupure totale des flux clients
        t_minus_1 = (base_time - timedelta(minutes=1)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_1,
                service="api-ingress",
                signal_type="trace",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "trace_id": "bb91234acfe1892182ffab23010b99de",
                    "span_id": "00a12e9cf31a",
                    "http_method": "GET",
                    "http_path": "/healthz",
                    "error_type": "SSL_HANDSHAKE_ERROR",
                    "error_message": "TLS Handshake failed: certificate_expired",
                },
            )
        )

        return ChaosScenarioResult(
            scenario_type=ChaosScenarioType.TLS_CERT_EXPIRY,
            title="TLS/SSL Certificate Expiry on Ingress",
            description=(
                "Expiration du certificat SSL du domaine d ingress api.k-oit.internal "
                "declenchant des erreurs ssl.SSLCertVerificationError et bloquant le "
                "handshake TLS de l ensemble des requetes entrantes du client."
            ),
            expected_root_cause="Expired SSL/TLS certificate for api.k-oit.internal on api-ingress",
            expected_severity=SeverityLevel.CRITICAL,
            signals=signals,
        )

    @classmethod
    def _generate_disk_full(cls, base_time: datetime) -> ChaosScenarioResult:
        """Simule la saturation d un point de montage disque (/var/log) sur audit-logging-node."""
        signals = []

        # T-5m : Espace disque disponible proche de zero
        t_minus_5 = (base_time - timedelta(minutes=5)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_5,
                service="audit-logging-node",
                signal_type="metric",
                severity=SeverityLevel.MAJOR,
                payload={
                    "metric_name": "disk_utilization_pct",
                    "mount_point": "/var/log",
                    "value": 99.2,
                    "available_bytes": 128000000,
                },
            )
        )

        # T-3m : Espace disque completement sature (100.0%)
        t_minus_3 = (base_time - timedelta(minutes=3)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_3,
                service="audit-logging-node",
                signal_type="metric",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "metric_name": "disk_utilization_pct",
                    "mount_point": "/var/log",
                    "value": 100.0,
                    "available_bytes": 0,
                },
            )
        )

        # T-2m : Exception OSError No space left dans les logs
        t_minus_2 = (base_time - timedelta(minutes=2)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_2,
                service="audit-logging-node",
                signal_type="log",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "logger": "audit.logger.file_writer",
                    "message": "OSError: [Errno 28] No space left on device: /var/log/audit/security_events.log",
                    "error_class": "OSError",
                    "errno": 28,
                },
            )
        )

        # T-1m : Blocage et verrouillage du service d audit de securite
        t_minus_1 = (base_time - timedelta(minutes=1)).isoformat()
        signals.append(
            TelemetrySignal(
                timestamp=t_minus_1,
                service="audit-logging-node",
                signal_type="trace",
                severity=SeverityLevel.CRITICAL,
                payload={
                    "trace_id": "782ca1a2f91bb2ea900cf8a31e8c0245",
                    "span_id": "e932b12cf302",
                    "operation": "log_security_audit_event",
                    "duration_ms": 60000.0,
                    "status": "FAILED",
                    "error_message": "Thread blocked: audit write buffer queue is full due to persistent disk write failure",
                },
            )
        )

        return ChaosScenarioResult(
            scenario_type=ChaosScenarioType.DISK_FULL,
            title="Disk Mount Point Partition Full",
            description=(
                "Saturation complete (100%) de l espace disque sur le point de montage "
                "/var/log d audit-logging-node, bloquant l ecriture des logs de securite "
                "avec une exception OSError: [Errno 28] No space left on device, "
                "bloquant et figeant l application."
            ),
            expected_root_cause="100% disk usage on /var/log mount point of audit-logging-node",
            expected_severity=SeverityLevel.CRITICAL,
            signals=signals,
        )
