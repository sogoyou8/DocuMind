# Local-only Airflow development image. Never deploy this image on Render Free.
FROM apache/airflow:3.4.0-python3.12
USER root
RUN mkdir -p /opt/airflow/state /opt/airflow/dags \
    && chown -R airflow:0 /opt/airflow/state /opt/airflow/dags \
    && chmod -R g=u /opt/airflow/state /opt/airflow/dags
COPY --chown=airflow:0 backend/requirements.txt backend/requirements-d2.txt /tmp/documind/
USER airflow
RUN pip install --no-cache-dir -r /tmp/documind/requirements-d2.txt
WORKDIR /opt/airflow
