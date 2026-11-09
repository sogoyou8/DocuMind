"""DocuMind D2: optional local Airflow DAG, every six hours plus manual trigger.

Requires Docker Compose --profile pipeline and the same local PostgreSQL
and mounted private uploads as the Django API. Does not run on Render.
"""
from datetime import timedelta
import os
import sys
import pendulum
from airflow.sdk import dag, task


@dag(
    dag_id="documind_d2_ingestion",
    schedule="0 */6 * * *",
    start_date=pendulum.datetime(2026, 11, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["documind", "d2", "local"],
)
def documind_d2_ingestion():
    @task(retries=2, retry_delay=timedelta(minutes=2),
          execution_timeout=timedelta(minutes=15))
    def process_received_documents():
        sys.path.insert(0, "/opt/documind/backend")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "documind_api.settings")
        import django
        django.setup()
        from django.core.management import call_command
        # Each operation is idempotent; Airflow retries are safe.
        call_command("process_pending", limit=20, verbosity=1)
        return "D2 batch completed"

    process_received_documents()


documind_d2_ingestion()
