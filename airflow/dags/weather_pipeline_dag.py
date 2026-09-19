from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor


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


# def validate_raw_data():
#     raise ValueError("Simulated failure to test callback")


def validate_raw_data():
    import json
    with open("/opt/airflow/project/data/weather_raw.json") as f:
        records = json.load(f)
    if not records:
        raise ValueError("weather_raw.json is empty — nothing to aggregate")
    print(f"Validation passed: {len(records)} records found")


def log_city_stats():
    import pandas as pd
    df = pd.read_csv("/opt/airflow/project/data/weather_summary.csv")
    for _, row in df.iterrows():
        print(f"{row['city']}: avg={row['avg_temp']}°C max={row['max_temp']}°C")


def on_task_failure(context):
    task_id = context["task_instance"].task_id
    dag_id = context["task_instance"].dag_id
    execution_date = context["execution_date"]
    print(f"ALERT: Task '{task_id}' in DAG '{dag_id}' failed at {execution_date}")
    print(f"Log URL: {context['task_instance'].log_url}")


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
    "on_failure_callback": on_task_failure,
}


with DAG(
    dag_id="weather_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 9, 1),
    schedule="@daily",
    catchup=False,
    tags=["weather", "pipeline"],
    dagrun_timeout=timedelta(minutes=10),
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_weather",
        python_callable=fetch_weather,
        retries=3,
        retry_delay=timedelta(seconds=30),
        retry_exponential_backoff=True,   # 30s, 60s, 120s
        execution_timeout=timedelta(minutes=5),
    )

    wait_for_raw_data = FileSensor(
        task_id="wait_for_raw_data",
        filepath="/opt/airflow/project/data/weather_raw.json",
        poke_interval=10,     # check every 10 seconds
        timeout=120,          # fail after 2 minutes
        mode="poke",
    )

    aggregate_task = PythonOperator(
        task_id="aggregate_weather",
        python_callable=aggregate_weather,
    )

    log_task = PythonOperator(
        task_id="log_city_stats",
        python_callable=log_city_stats,
    )

    validate_task = PythonOperator(
        task_id="validate_raw_data",
        python_callable=validate_raw_data,
    )

    dbt_task = BashOperator(
        task_id="run_dbt",
        bash_command="cd /opt/airflow/project/weather_dbt && dbt run --profiles-dir .",
    )

    fetch_task >> wait_for_raw_data >> validate_task >> aggregate_task >> [dbt_task, log_task]
