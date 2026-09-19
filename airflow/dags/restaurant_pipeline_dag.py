from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor


def on_task_failure(context):
    task_id = context["task_instance"].task_id
    dag_id = context["task_instance"].dag_id
    execution_date = context["execution_date"]
    print(f"ALERT: Task '{task_id}' in DAG '{
          dag_id}' failed at {execution_date}")
    print(f"Log URL: {context['task_instance'].log_url}")


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
    "on_failure_callback": on_task_failure,
}


def generate_orders():
    import json
    import random
    from datetime import date

    restaurants = ["Pizza Palace", "Burger Barn", "Sushi Stop", "Taco Town"]
    cities = ["cairo", "dubai", "riyadh", "alexandria"]
    statuses = ["delivered", "cancelled"]

    orders = []
    for i in range(1, 21):
        orders.append({
            "order_id": i,
            "restaurant_name": random.choice(restaurants),
            "city": random.choice(cities),
            "amount": round(random.uniform(5.0, 100.0), 2),
            "status": random.choices(statuses, weights=[8, 2])[0],
            "order_date": str(date.today()),
        })

    output_path = "/opt/airflow/project/data/restaurant_orders.json"
    with open(output_path, "w") as f:
        json.dump(orders, f)

    print(f"Generated {len(orders)} orders")


def validate_orders():
    import json
    required_fields = ["order_id", "restaurant_name", "amount"]
    with open("/opt/airflow/project/data/restaurant_orders.json") as f:
        records = json.load(f)
    if not records:
        raise ValueError(
            "restaurant_orders.json is empty — nothing to aggregate")

    for r in records:
        for field in required_fields:
            if r.get(field) is None:
                raise ValueError(
                    f"record {r.get('order_id')} is missing field: {field}.")
    print(f"Validation passed: {len(records)} records found")


def load_orders():
    import sys
    sys.path.insert(0, "/opt/airflow/project")
    import duckdb
    import json

    db_path = "/opt/airflow/project/data/warehouse.db"
    raw_path = "/opt/airflow/project/data/restaurant_orders.json"

    with open(raw_path) as f:
        records = json.load(f)

    with duckdb.connect(db_path) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS restaurant_orders_raw (
                order_id        INTEGER,
                restaurant_name VARCHAR,
                city            VARCHAR,
                amount          DOUBLE,
                status          VARCHAR,
                order_date      VARCHAR
            )
        """)
        con.execute("DELETE FROM restaurant_orders_raw")
        for r in records:
            con.execute(
                "INSERT INTO restaurant_orders_raw VALUES (?, ?, ?, ?, ?, ?)",
                [r.get("order_id"), r.get("restaurant_name"), r.get(
                    "city"), r.get("amount"), r.get("status"), r.get("order_date")]
            )
        count = con.execute(
            "SELECT COUNT(*) FROM restaurant_orders_raw").fetchone()[0]
        print(f"Loaded {count} rows into weather_raw")


with DAG(
    dag_id="restaurant_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 9, 1),
    schedule="@daily",
    catchup=False,
    tags=["restaurant", "pipeline"],
    dagrun_timeout=timedelta(minutes=15),
) as dag:
    generate_task = PythonOperator(
        task_id="generate_orders",
        python_callable=generate_orders,
        retries=3,
        retry_delay=timedelta(seconds=30),
        retry_exponential_backoff=True,   # 30s, 60s, 120s
        execution_timeout=timedelta(minutes=5),
    )

    validate_task = PythonOperator(
        task_id="validate_orders",
        python_callable=validate_orders
    )

    load_task = PythonOperator(
        task_id="load_orders",
        python_callable=load_orders
    )

    dbt_task = BashOperator(
        task_id="run_dbt",
        bash_command="cd /opt/airflow/project/weather_dbt && dbt run --select restaurant_* --profiles-dir /opt/airflow/project/airflow/",
    )

    generate_task >> validate_task >> load_task >> dbt_task
