# K-OIT — Operations Incident Triage

[![GCP europe-west9](https://img.shields.io/badge/GCP_Region-europe--west9_(Paris)-blue?logo=googlecloud&logoColor=white)](https://cloud.google.com/about/locations/paris)
[![Google ADK 2.0](https://img.shields.io/badge/Google_ADK-2.0-4285F4?logo=google&logoColor=white)](https://cloud.google.com/products/agent-development-kit)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Agent Card A2A](https://img.shields.io/badge/A2A_Protocol-Agent_Card_JSON-cyan)](docs/agent-card.json)
[![SRE Accuracy](https://img.shields.io/badge/Root_Cause_Accuracy-100%25-brightgreen)](artifacts/sre_eval_report.md)
[![MTTR Reduction](https://img.shields.io/badge/MTTR_Reduction--75%25-brightgreen)](artifacts/sre_eval_report.md)

> **Autonomous SRE Copilot & Multi-Signal Incident Triage Engine for Cloud-Native Distributed Architectures on Google Cloud Platform.**

Developed by **[Kerdjou Tigroudja](https://kerdjou.dev)** (`contact@kerdjou.dev`).

---

## Executive Overview

**K-OIT (Operations Incident Triage)** is an enterprise-grade autonomous SRE system designed to help engineering and on-call operations teams rapidly detect, correlate, and triage production incidents across complex distributed cloud architectures (GCP, GKE, Cloud Run).

### Key Differentiators:
1. **Strict European Data Sovereignty :** Compute (Cloud Run), telemetry datasets (BigQuery Agent Analytics), logging sinks (Cloud Logging), and trace storage are hosted strictly in the **`europe-west9` (Paris, France)** sovereign cloud region.
2. **Multi-Source OpenTelemetry Ingestion & Causal Isolation :** Continuously processes distributed traces, metrics, and structured logs. Deterministically isolates the actual root cause from downstream cascading collateral symptoms (e.g. database pool exhaustion vs frontend 504 gateway timeouts).
3. **Chaos Engineering Simulator Testbed :** Built-in industrial chaos generator reproducing 5 major production failure modes (`db_pool_exhaustion`, `oom_crash`, `upstream_api_timeout`, `tls_cert_expiry`, `disk_full`).
4. **Human-in-the-Loop SRE Safety Gates :** Enforces strict read-only and non-destructive incident assessment. Generates validated mitigation runbooks with rollback scripts and non-destructive verification commands, submitted for explicit on-call engineer validation.
5. **Zero-Trust Security & Private IAM :** Cloud Run endpoints enforce private IAM invoker controls (`roles/run.invoker`), rejecting unauthenticated public requests by design (HTTP 403 Forbidden).

---

## System Architecture

```mermaid
graph TD
    classDef client fill:#E1F5FE,stroke:#0288D1,stroke-width:2px,color:#000;
    classDef agent fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
    classDef gcp fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000;
    classDef hitl fill:#EDE7F6,stroke:#512DA8,stroke-width:2px,color:#000;

    Client["OTel Collector / Alertmanager / CI/CD"]:::client

    subgraph CloudRun ["Cloud Run Service (europe-west9)"]
        FastAPIApp["FastAPI Server & A2A Handler<br>/a2a/app/.well-known/agent-card.json"]:::agent
        Orchestrator["Root SRE Orchestrator Agent<br>(Google ADK 2.0 / Gemini 3.7 Flash)"]:::agent
        
        Ingestion["Telemetry Ingestion Engine<br>(OTel Metrics, Logs, Traces)"]:::agent
        Correlator["Causal Graph Correlator<br>(Root Cause vs Symptoms)"]:::agent
        Diagnostician["Incident Diagnostician<br>(Severity & Blast Radius)"]:::agent
        Advisor["SRE Mitigation Advisor<br>(Runbook, Verification, Rollback)"]:::agent
        ChaosEngine["Chaos Simulator Engine<br>(5 Production Scenarios)"]:::agent
        
        Orchestrator --> Ingestion
        Ingestion --> Correlator
        Correlator --> Diagnostician
        Diagnostician --> Advisor
        ChaosEngine -.->|Injects Synthetic Chaos Telemetry| Ingestion
    end

    subgraph SovereignStorage ["GCP Sovereign Infrastructure (europe-west9)"]
        BigQuery[("BigQuery Agent Analytics<br>Token Metrics, Tool Calls, FinOps")]:::gcp
        CloudLogging["Cloud Logging & Audit Sinks"]:::gcp
        CloudRunNode["Cloud Run Serverless Compute"]:::gcp
    end

    subgraph HumanApprovalGate ["Human-in-the-Loop Operational Gate"]
        OnCallSRE["On-Call SRE Engineer<br>(Review & Decision Authority)"]:::hitl
        MitigationRunbook["Validated Mitigation Runbook<br>(Rollback & Verification Scripts)"]:::hitl
    end

    Client --> FastAPIApp
    FastAPIApp --> Orchestrator
    Orchestrator -.->|Sanitized Spans & Metrics| BigQuery
    Orchestrator -.->|System Audit Logs| CloudLogging
    Advisor -->|Proposes Action Plan (human_approval_required=True)| OnCallSRE
    OnCallSRE -->|Approves & Executes| MitigationRunbook
```

---

## Live Production & A2A Endpoints

| Resource | Description | Location / Access |
|---|---|---|
| **A2A Agent Card** | Machine-readable capabilities descriptor | [docs/agent-card.json](docs/agent-card.json) |
| **Cloud Run Production Service** | Authenticated Serverless Node | `europe-west9 (Paris, France)` |
| **Evaluation Benchmark Report** | SRE Golden Set (10/10 PASS) | [artifacts/sre_eval_report.md](artifacts/sre_eval_report.md) |
| **A2A JSON-RPC Streaming** | Agent execution endpoint | `/a2a/app` (IAM Authenticated) |

> [!NOTE]
> **Security Notice (Zero-Trust Ingress) :** In alignment with SecNumCloud isolation principles and enterprise Zero-Trust architectures, the live Cloud Run service enforces private IAM authentication (`roles/run.invoker`). Unauthenticated requests are rejected by design (HTTP 403 Forbidden). Authorized clients pass a Google Cloud OAuth2 Bearer token in the `Authorization` header.

---

## SRE Golden Set Evaluation Benchmark

K-OIT is calibrated against an enterprise SRE Golden Set benchmark comprising 10 multi-stage incident scenarios (cascading failures, concurrency bottlenecks, downstream outages).

| Metric | Result | Benchmark Target | Verdict |
|---|---|---|---|
| **Scenario Completion Rate** | $10/10\text{ (100.0\%)}$ | $\ge 90.0\%$ | **PASS** |
| **Root Cause Isolation Accuracy** | $100.0\%$ | $\ge 95.0\%$ | **PASS** |
| **Simulated MTTR Reduction** | $75.0\%$ | $\ge 50.0\%$ | **PASS** |
| **Average Decision Latency** | $0.15\text{ ms}$ | $\le 500\text{ ms}$ | **PASS** |
| **Human Approval Enforcement** | $100.0\%$ | $100.0\%$ | **PASS** |

Detailed execution report and trace evidence are documented in [`artifacts/sre_eval_report.md`](artifacts/sre_eval_report.md).

---

## Local Quickstart & Test Suite

### 1. Prerequisites
- Python 3.12+
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### 2. Setup & Installation
```bash
git clone https://github.com/kerdjou-tigroudja/k-oit-showcase.git
cd k-oit-showcase

# Install dependencies in isolated virtual environment
uv sync
```

### 3. Run Autonomous Unit Test Suite (14 tests, 100% Mocked/Offline)
```bash
uv run pytest tests/unit/ -v
```

### 4. Run SRE Golden Set Evaluation Benchmark
```bash
uv run python eval/run_sre_benchmark.py
```

---

## Architectural Decision Records (MADR)

Key architectural decisions are documented in [`docs/adr/`](docs/adr/):
- **[ADR-001: Sovereign Agentic Architecture for SRE Incident Triage using Google ADK 2.0](docs/adr/ADR-001-sovereign-adk-sre-architecture.md)**
- **[ADR-002: Deterministic Causal Correlation Engine and Chaos Simulator Benchmark](docs/adr/ADR-002-deterministic-causal-correlation-and-chaos-simulator.md)**
- **[ADR-003: Human-in-the-Loop Safety Gates for SRE Mitigation Actions](docs/adr/ADR-003-human-in-the-loop-sre-mitigation-protocol.md)**

---

## Related Repositories & Portfolio

* **Sovereign Compliance Mesh Showcase :** [`kerdjou-tigroudja/k-scm-showcase`](https://github.com/kerdjou-tigroudja/k-scm-showcase)
* **Official Web Hub :** [https://kerdjou.dev](https://kerdjou.dev)
* **Author Contact :** [contact@kerdjou.dev](mailto:contact@kerdjou.dev)
