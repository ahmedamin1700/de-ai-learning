from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "retries": 1,
}


def fetch_weather():
    import sys
    sys.path.insert(0, "/opt/airflow/project")
    from src.api.weather import fetch_cities
    from src.io.file_ops import write_json
    import yaml

    with open("/opt/airflow/project/config/cities.yaml") as f:
        config = yaml.safe_load(f)

    cities = [
        {"name": name, **coords}
        for name, coords in config.get("cities", {}).items()
    ]
    records = fetch_cities(cities)
    write_json(records, "/opt/airflow/project/data/weather_raw.json")
    print(f"Fetched {len(records)} records")


def aggregate_weather():
    import sys
    sys.path.insert(0, "/opt/airflow/project")
    import json
    import pandas as pd
    from src.utils.dataframe_ops import aggregate_weather

    with open("/opt/airflow/project/data/weather_raw.json") as f:
        records = json.load(f)

    df = pd.DataFrame(records)
    summary = aggregate_weather(df)
    summary.to_csv(
        "/opt/airflow/project/data/weather_summary.csv", index=False)
    print(f"Aggregated {len(summary)} cities")


with DAG(
    dag_id="weather_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 9, 1),
    schedule="@daily",
    catchup=False,
    tags=["weather", "pipeline"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_weather",
        python_callable=fetch_weather,
    )

    aggregate_task = PythonOperator(
        task_id="aggregate_weather",
        python_callable=aggregate_weather,
    )

    dbt_task = BashOperator(
        task_id="run_dbt",
        bash_command="cd /opt/airflow/project/weather_dbt && dbt run --profiles-dir .",
    )

    fetch_task >> aggregate_task >> dbt_task
