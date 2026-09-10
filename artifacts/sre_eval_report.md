# Rapport d'Evaluation SRE - K-OIT Golden Set

- **Nombre total de cas evalues :** 10
- **Taux de reussite global :** 10/10 ($100\%$)
- **Precision de la cause racine (Root Cause Accuracy) :** $100.0\%$
- **Precision de la severite (Severity Accuracy) :** $100.0\%$
- **Taux d'isolation des symptomes collateraux :** $100.0\%$
- **Conformite Human-in-the-Loop :** $100.0\%$
- **Latence moyenne de traitement :** $0.26\text{ ms}$
- **Reduction du MTTR simule :** $75.0\%$ (de $45\text{ min}$ a $11.25\text{ min}$)

## Detail des Cas d'Evaluation

| ID | Scenario | Service Racine | Severite | HITL | Latence | Verdict |
|---|---|---|---|---|---|---|
| sre_db_pool_01 | `db_pool_exhaustion` | `order-service` | CRITICAL | True | $0.59\text{ ms}$ | **PASS** |
| sre_db_pool_02 | `db_pool_exhaustion` | `order-service` | CRITICAL | True | $0.3\text{ ms}$ | **PASS** |
| sre_oom_01 | `oom_crash` | `recommendation-worker` | CRITICAL | True | $0.27\text{ ms}$ | **PASS** |
| sre_oom_02 | `oom_crash` | `recommendation-worker` | CRITICAL | True | $0.19\text{ ms}$ | **PASS** |
| sre_upstream_01 | `upstream_api_timeout` | `payment-service` | CRITICAL | True | $0.18\text{ ms}$ | **PASS** |
| sre_upstream_02 | `upstream_api_timeout` | `payment-service` | CRITICAL | True | $0.35\text{ ms}$ | **PASS** |
| sre_tls_01 | `tls_cert_expiry` | `api-ingress` | CRITICAL | True | $0.17\text{ ms}$ | **PASS** |
| sre_tls_02 | `tls_cert_expiry` | `api-ingress` | CRITICAL | True | $0.14\text{ ms}$ | **PASS** |
| sre_disk_01 | `disk_full` | `audit-logging-node` | CRITICAL | True | $0.2\text{ ms}$ | **PASS** |
| sre_disk_02 | `disk_full` | `audit-logging-node` | CRITICAL | True | $0.19\text{ ms}$ | **PASS** |
