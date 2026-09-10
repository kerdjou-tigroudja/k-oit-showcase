"""Unit test for SRE benchmark runner."""

from eval.run_sre_benchmark import run_benchmark


def test_sre_benchmark_execution():
    summary = run_benchmark()
    assert summary["total_cases"] == 10
    assert summary["passed_cases"] == 10
    assert summary["root_cause_accuracy_percent"] == 100.0
    assert summary["severity_accuracy_percent"] == 100.0
    assert summary["symptom_isolation_rate_percent"] == 100.0
    assert summary["human_in_the_loop_compliance_percent"] == 100.0
    assert summary["mttr_reduction_percent"] >= 70.0
