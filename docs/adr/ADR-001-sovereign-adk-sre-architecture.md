# ADR-001: Sovereign Agentic Architecture for SRE Incident Triage using Google ADK 2.0

* **Status:** Accepted
* **Deciders:** Kerdjou Tigroudja (Lead Cloud Security & Sovereign AI Systems Engineer)
* **Date:** 2026-08-25

## Context and Problem Statement
Distributed cloud architectures (GKE, Cloud Run, microservices) generate massive volumes of disparate telemetry signals during production outages. Manual triage under crisis conditions results in prolonged Mean Time To Resolution (MTTR 20 to 45 minutes) and severe alert fatigue. We need an automated SRE copilot capable of high-throughput telemetry ingestion, causal diagnosis, and rapid remediation advice, while strictly adhering to European data sovereignty and SecNumCloud compliance.

## Decision Drivers
* Native integration with Google Agent Development Kit (ADK 2.0) and A2A (Agent-to-Agent) protocol.
* Ultra-low latency LLM inference using Gemini 3.7 Flash for near-real-time triage.
* Strict data residency within the `europe-west9` (Paris, France) sovereign cloud perimeter.
* Granular FinOps auditability and interaction tracking via BigQuery Agent Analytics (`adk_agent_analytics`).
* Zero-Trust IAM security (`roles/run.invoker`) preventing unauthorized invocation.

## Considered Options
1. Traditional alert correlation rules engines without AI reasoning.
2. Self-hosted open-source LLMs on GPU compute clusters.
3. Managed Google Cloud ADK 2.0 on Cloud Run with Gemini 3.7 Flash in `europe-west9`.

## Decision Outcome
Chosen option: **Managed Google Cloud ADK 2.0 on Cloud Run with Gemini 3.7 Flash in `europe-west9`**, because:
* Fully managed serverless scalability with zero cold-start penalty for critical incident events.
* Complete isolation within the Parisian sovereign zone (`europe-west9`).
* Native export of all agent traces, tool executions, and token metrics to BigQuery Agent Analytics for compliance and FinOps governance.
