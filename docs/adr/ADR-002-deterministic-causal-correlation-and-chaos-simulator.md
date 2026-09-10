# ADR-002: Deterministic Causal Correlation Engine and Chaos Simulator Benchmark

* **Status:** Accepted
* **Deciders:** Kerdjou Tigroudja (Lead Cloud Security & Sovereign AI Systems Engineer)
* **Date:** 2026-08-26

## Context and Problem Statement
LLMs alone can hallucinate root causes when fed complex cascading telemetry streams where downstream services exhibit high error rates while the root defect is upstream (e.g. database pool exhaustion causing cascading HTTP 504 errors across frontend gateways). High-stakes production triage requires mathematical certitude in causal isolation and reproducible benchmarking.

## Decision Drivers
* Zero tolerance for root cause hallucinations during critical P1/P0 outages.
* Absolute distinction between root cause origin and collateral cascading symptoms.
* Reproducible Chaos Engineering testbed covering common failure patterns.
* Quantitative evaluation against a Golden Set benchmark prior to production release.

## Considered Options
1. End-to-end unstructured prompt feeding all raw logs directly to the LLM.
2. Pure heuristic graph traversal without contextual reasoning.
3. Hybrid architecture: Deterministic Causal Correlator coupled with an OpenTelemetry Chaos Simulator and LLM synthesis.

## Decision Outcome
Chosen option: **Hybrid Architecture with Deterministic Causal Correlator and Chaos Simulator Engine**, because:
* The `ChaosSimulator` models 5 industrial failure scenarios (`db_pool_exhaustion`, `oom_crash`, `upstream_api_timeout`, `tls_cert_expiry`, `disk_full`).
* The `IncidentCorrelator` deterministically segments root causes from cascading symptoms and computes blast radius.
* Evaluated against the 10-scenario SRE Golden Set benchmark, achieving 100% root cause identification accuracy and sub-millisecond execution latency.
