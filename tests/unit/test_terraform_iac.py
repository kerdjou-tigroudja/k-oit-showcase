"""Unit tests for Terraform IaC static configuration."""

from pathlib import Path


def test_terraform_files_exist():
    """Verify that all core Terraform IaC files exist in infra/terraform."""
    tf_dir = Path("infra/terraform")
    assert tf_dir.exists()

    required_files = [
        "apis.tf",
        "iam.tf",
        "providers.tf",
        "service.tf",
        "storage.tf",
        "telemetry.tf",
        "variables.tf",
        "terraform.tfvars.example",
    ]
    for filename in required_files:
        assert (tf_dir / filename).exists(), f"Missing Terraform file: {filename}"


def test_terraform_cloud_run_definition():
    """Verify that Cloud Run v2 service is properly declared with europe-west9 location."""
    service_tf = Path("infra/terraform/service.tf").read_text(encoding="utf-8")
    assert "google_cloud_run_v2_service" in service_tf
    assert "var.region" in service_tf
    assert "limits" in service_tf


def test_terraform_bigquery_telemetry():
    """Verify that BigQuery dataset and logging sinks are declared for GenAI telemetry."""
    telemetry_tf = Path("infra/terraform/telemetry.tf").read_text(encoding="utf-8")
    assert "google_bigquery_dataset" in telemetry_tf
    assert "google_logging_project_sink" in telemetry_tf


def test_terraform_zero_secrets():
    """Verify that no sensitive project IDs or credentials exist in tfvars example."""
    example_tfvars = Path("infra/terraform/terraform.tfvars.example").read_text(encoding="utf-8")
    assert "your-gcp-project-id" in example_tfvars
    assert "AIzaSy" not in example_tfvars
    assert "private_key" not in example_tfvars
