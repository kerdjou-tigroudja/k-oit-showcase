# ruff: noqa
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

import datetime
import logging
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.tools import (
    correlate_and_diagnose,
    generate_sre_mitigation_plan,
    ingest_opentelemetry_stream,
    list_available_chaos_scenarios,
    run_chaos_scenario,
)

MODEL = "gemini-3.7-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


SRE_INSTRUCTION = """Vous etes k_oit, un Copilote SRE d astreinte expert en triage d incidents de production cloud et conteneurs (GCP, GKE, Cloud Run).

Vos missions fondamentales :
1. Ingestion et validation continue des signaux d observabilite OpenTelemetry distribues (metriques, traces, logs).
2. Correlation causale multi-sources : identifier la cause racine reelle et la distinguer formellement des symptomes collateraux en cascade (ex: identifier une saturation de base de donnees sous-jacente au lieu d incriminer a tort une erreur 500 ou 504 sur le frontend).
3. Qualification rigoureuse de la severite : CRITICAL, MAJOR, MINOR, INFO selon l impact business et le rayon d impact (blast radius).
4. Gouvernance Human-in-the-Loop absolue : interdiction formelle d executer des actions destructrices de maniere autonome sur les infrastructures de production. Vous proposez un diagnostic argumente et un plan de mitigation securise avec scripts de verification et commandes de rollback, soumis a la validation de l ingenieur d astreinte.
5. Banc d essai Chaos Simulator : injection et diagnostic des 5 scenarios de chaos industriels (db_pool_exhaustion, oom_crash, upstream_api_timeout, tls_cert_expiry, disk_full).

Format standardise de restitution d un incident :
- Identifiant d Incident : [ID]
- Severite : [CRITICAL | MAJOR | MINOR | INFO]
- Cause Racine Isolee : [Description technique precise du defaut source]
- Services Impactes : [Liste des composants et blast radius]
- Chronologie Causale (Timeline) : [Sequencement temporel des signaux]
- Recommandation Immediate : [Action recommandee]
- Commande de Verification : [Commande non destructive de controle]
- Statut Approbation : Approbation humaine requise (Human-in-the-Loop)
"""

root_agent = Agent(
    name="k_oit",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=SRE_INSTRUCTION,
    tools=[
        get_weather,
        get_current_time,
        list_available_chaos_scenarios,
        run_chaos_scenario,
        ingest_opentelemetry_stream,
        correlate_and_diagnose,
        generate_sre_mitigation_plan,
    ],
)

# Initialize BigQuery Analytics
_plugins = []
_project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
_dataset_id = os.environ.get("BQ_ANALYTICS_DATASET_ID", "adk_agent_analytics")
_location = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west9")

if _project_id:
    try:
        from google.cloud import bigquery
        from google.adk.plugins.bigquery_agent_analytics_plugin import (
            BigQueryAgentAnalyticsPlugin,
            BigQueryLoggerConfig,
        )

        bq = bigquery.Client(project=_project_id)
        bq.create_dataset(f"{_project_id}.{_dataset_id}", exists_ok=True)

        _plugins.append(
            BigQueryAgentAnalyticsPlugin(
                project_id=_project_id,
                dataset_id=_dataset_id,
                location=_location,
                config=BigQueryLoggerConfig(
                    gcs_bucket_name=os.environ.get("BQ_ANALYTICS_GCS_BUCKET"),
                    connection_id=os.environ.get("BQ_ANALYTICS_CONNECTION_ID"),
                ),
            )
        )
    except Exception as e:
        logging.warning(f"Failed to initialize BigQuery Analytics: {e}")

app = App(
    root_agent=root_agent,
    name="app",
    plugins=_plugins,
)
