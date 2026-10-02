-- Load stub for google_bigquery_table.completions_view.
-- Every template variable passed by telemetry.tf is referenced so templatefile() succeeds.
-- The join matches nothing; it only keeps Terraform able to load this path.
SELECT
  logs.timestamp
FROM `${project_id}.${dataset_id}.${genai_logs_table}` AS logs
LEFT JOIN `${project_id}.${dataset_id}.${completions_external_table}` AS completions
  ON FALSE
