import duckdb
import logging
from rich.console import Console
from rich.table import Table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_warehouse(db_path: str) -> None:
    with duckdb.connect(db_path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                city VARCHAR NOT NULL,
                amount DOUBLE,
                status VARCHAR,
                is_high_value BOOLEAN
            )
            """
        )
        logger.info("Orders table created.")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS weather_summary (
                city VARCHAR PRIMARY KEY,
                avg_temp DOUBLE,
                max_temp DOUBLE,
                min_temp DOUBLE,
                record_count INTEGER
            )
            """
        )
        logger.info("Weather Summary table created.")


def load_orders(db_path: str, csv_path: str) -> int:
    with duckdb.connect(db_path) as con:
        result = con.execute(
            f"""
            INSERT OR REPLACE INTO orders
            SELECT
                id,
                TRIM(LOWER(city)) AS city,
                TRY_CAST(amount AS DOUBLE) AS amount,
                status,
                CASE
                    WHEN TRY_CAST(amount AS DOUBLE) > 50 THEN TRUE
                    ELSE FALSE
                END AS is_high_value
            FROM read_csv_auto('{csv_path}')
            WHERE TRY_CAST(amount AS DOUBLE) IS NOT NULL
              AND city IS NOT NULL
              AND TRIM(city) != ''
            RETURNING *;
            """
        ).fetchall()
    return len(result)


def load_weather(db_path: str, json_path: str) -> int:
    with duckdb.connect(db_path) as con:
        result = con.execute(
            f"""
            INSERT OR REPLACE INTO weather_summary
            SELECT
                TRIM(LOWER(city)) AS city,
                ROUND(AVG(temperature_c), 1) AS avg_temp,
                MAX(temperature_c) AS max_temp,
                MIN(temperature_c) AS min_temp,
                COUNT(*) AS record_count
            FROM read_json_auto('{json_path}')
            GROUP BY TRIM(LOWER(city))
            RETURNING *;
            """
        ).fetchall()
    return len(result)


def query_enriched(db_path: str) -> None:
    with duckdb.connect(db_path) as con:
        result = con.execute(
            """
            SELECT
                o.*,
                w.avg_temp,
                w.max_temp,
                w.min_temp,
                w.record_count
            FROM orders AS o
            LEFT JOIN weather_summary AS w
            ON o.city = w.city
            ORDER BY o.id ASC;
            """
        ).fetchall()

    console = Console()
    table = Table()
    table.add_column("id")
    table.add_column("city")
    table.add_column("amount")
    table.add_column("status")
    table.add_column("is_high_value")
    table.add_column("avg_temp")
    table.add_column("max_temp")
    table.add_column("min_temp")
    table.add_column("record_count")

    for id, city, amount, status, is_high_value, avg_temp, max_temp, min_temp, record_count in result:
        table.add_row(
            str(id),
            str(city),
            str(amount),
            str(status),
            str(is_high_value),
            str(avg_temp),
            str(max_temp),
            str(min_temp),
            str(record_count),
        )
    console.print(table)


if __name__ == "__main__":
    DB = "data/warehouse.db"
    create_warehouse(DB)
    n = load_orders(DB, "data/raw/orders.csv")
    logger.info(f"Loaded {n} orders")
    n = load_weather(DB, "data/raw/weather.json")
    logger.info(f"Loaded {n} weather summaries")
    query_enriched(DB)
