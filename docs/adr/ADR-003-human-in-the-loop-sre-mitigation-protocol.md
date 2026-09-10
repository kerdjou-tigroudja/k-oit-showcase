# ADR-003: Human-in-the-Loop Safety Gates for SRE Mitigation Actions

* **Status:** Accepted
* **Deciders:** Kerdjou Tigroudja (Lead Cloud Security & Sovereign AI Systems Engineer)
* **Date:** 2026-08-27

## Context and Problem Statement
Autonomous remediation systems that execute write or restart actions on production infrastructure without human supervision present extreme operational risks. An incorrect automated rollback or container restart during a split-brain condition can destroy persistent state or trigger irreversible cascade failures.

## Decision Drivers
* Prevention of catastrophic unintended automated actions in production clusters.
* Strict separation of advisory synthesis from remediation execution.
* Auditability of recommended actions, verification scripts, and rollback steps.
* SRE on-call engineer final decision authority.

## Considered Options
1. Full autonomous self-healing without human intervention.
2. Purely passive diagnostic reporting without actionable runbook generation.
3. Human-in-the-Loop (HITL) supervised protocol with structured executable runbooks.

## Decision Outcome
Chosen option: **Human-in-the-Loop Supervised Protocol**, because:
* All generated `MitigationPlan` models enforce `human_approval_required = True`.
* The agent provides deterministic verification commands (`verification_script`) and rollback commands (`rollback_commands`), empowering the on-call engineer with immediate, safe execution artifacts.
* Mitigates MTTR while preserving complete human operational control.
