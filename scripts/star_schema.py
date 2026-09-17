import duckdb
import logging
from rich.console import Console
from rich.table import Table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

DB = "data/warehouse.db"

# STAR SCHEMA DESIGN
# ==================
#
# fact_orders
#   - order_key     (PK, surrogate integer)
#   - date_key      (FK → dim_date.date_key)
#   - city_key      (FK → dim_city.city_key)
#   - status_key    (FK → dim_status.status_key)
#   - amount        (DOUBLE)
#   - is_high_value (BOOLEAN)
#
# dim_date
#   - date_key    (PK) -- YYYYMMDD integer e.g. 20260901
#   - date        (DATE)
#   - day_of_week
#   - week_number
#   - month_name
#   - quarter
#   - year
#   - is_weekend
#
# dim_city
#   - city_key  (PK, surrogate integer)
#   - name
#
# dim_status
#   - status_key  (PK, surrogate integer)
#   - status


def run_query(title: str, query: str, columns: list[str]) -> None:
    """Run a SQL query and print results as a rich table."""
    with duckdb.connect(DB) as con:
        rows = con.execute(query).fetchall()

    table = Table(title=title)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(v) for v in row])
    console.print(table)
    console.print()


def create_star_schema(db_path: str) -> None:
    """Create all 4 star schema tables if they don't exist."""
    with duckdb.connect(db_path) as con:

        # TODO: CREATE TABLE IF NOT EXISTS dim_date (...)
        # Columns: date_key INTEGER PRIMARY KEY, date DATE, day_of_week VARCHAR,
        #          week_number INTEGER, month_name VARCHAR, quarter INTEGER,
        #          year INTEGER, is_weekend BOOLEAN
        query = """
        CREATE TABLE IF NOT EXISTS dim_date (
            date_key INTEGER PRIMARY KEY,
            date DATE,
            day_of_week VARCHAR,
            week_number INTEGER,
            month_name VARCHAR,
            quarter INTEGER,
            year INTEGER,
            is_weekend BOOLEAN
        )
        """
        con.execute(query=query)

        # TODO: CREATE TABLE IF NOT EXISTS dim_city (...)
        # Columns: city_key INTEGER PRIMARY KEY, city_name VARCHAR
        query = """
        CREATE TABLE IF NOT EXISTS dim_city (
            city_key INTEGER PRIMARY KEY,
            city_name VARCHAR
        )
        """
        con.execute(query=query)

        # TODO: CREATE TABLE IF NOT EXISTS dim_status (...)
        # Columns: status_key INTEGER PRIMARY KEY, status_name VARCHAR
        query = """
        CREATE TABLE IF NOT EXISTS dim_status (
            status_key INTEGER PRIMARY KEY,
            status_name VARCHAR
        )
        """
        con.execute(query=query)

        # TODO: CREATE TABLE IF NOT EXISTS fact_orders (...)
        # Columns: order_key INTEGER PRIMARY KEY, date_key INTEGER, city_key INTEGER,
        #          status_key INTEGER, amount DOUBLE, is_high_value BOOLEAN
        query = """
        CREATE TABLE IF NOT EXISTS fact_orders (
            order_key INTEGER PRIMARY KEY,
            date_key INTEGER,
            city_key INTEGER,
            status_key INTEGER,
            amount DOUBLE,
            is_high_value BOOLEAN
        )
        """
        con.execute(query=query)

        logger.info("Star schema tables created.")


def load_dimensions(db_path: str) -> None:
    """Populate dim_date, dim_city, and dim_status."""
    with duckdb.connect(db_path) as con:

        # --- dim_date ---
        # TODO: Use a recursive CTE to generate dates from 2026-09-01 to 2026-09-30
        # For each date compute:
        #   date_key   → CAST(strftime(date, '%Y%m%d') AS INTEGER)
        #   day_of_week → dayname(date)
        #   week_number → weekofyear(date)
        #   month_name  → monthname(date)
        #   quarter     → quarter(date)
        #   year        → year(date)
        #   is_weekend  → dayofweek(date) IN (1, 7)  -- 1=Sunday, 7=Saturday in DuckDB
        # INSERT OR REPLACE INTO dim_date SELECT ... FROM the CTE
        query = """
        WITH RECURSIVE date_series AS (
            SELECT DATE '2026-09-01' AS date
            UNION ALL
            SELECT date + INTERVAL 1 DAY
            FROM date_series
            WHERE DATE < DATE '2026-09-30'
        )
        INSERT OR REPLACE INTO dim_date
        SELECT
            CAST(strftime(date, '%Y%m%d') AS INTEGER),
            date,
            DAYNAME(date),
            WEEKOFYEAR(date),
            MONTHNAME(date),
            QUARTER(date),
            YEAR(date),
            DAYOFWEEK(date) IN (0, 6)
        FROM date_series
        """
        con.execute(query=query)
        logger.info("dim_date loaded.")

        # --- dim_city ---
        # TODO: INSERT OR REPLACE INTO dim_city
        # SELECT ROW_NUMBER() OVER (ORDER BY city) AS city_key, city AS city_name
        # FROM (SELECT DISTINCT city FROM deliveries)
        query = """
        INSERT OR REPLACE INTO dim_city
        WITH unique_cities AS (
            SELECT DISTINCT
            city
            FROM deliveries
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY city) AS city_key,
            city AS city_name
        FROM unique_cities
        """
        con.execute(query=query)
        logger.info("dim_city loaded.")

        # --- dim_status ---
        # TODO: INSERT OR REPLACE INTO dim_status
        # SELECT ROW_NUMBER() OVER (ORDER BY status) AS status_key, status AS status_name
        # FROM (SELECT DISTINCT status FROM deliveries)
        query = """
        INSERT OR REPLACE INTO dim_status
        WITH unique_status AS (
            SELECT DISTINCT
            status
            FROM deliveries
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY status) AS status_key,
            status AS status_name
        FROM unique_status
        """
        con.execute(query=query)
        logger.info("dim_status loaded.")


def load_facts(db_path: str) -> None:
    """Populate fact_orders by joining deliveries with dimension tables."""
    with duckdb.connect(db_path) as con:

        # TODO: INSERT OR REPLACE INTO fact_orders
        # Join deliveries with dim_date ON date = order_date
        # Join deliveries with dim_city ON city_name = city
        # Join deliveries with dim_status ON status_name = status
        # SELECT:
        #   id AS order_key
        #   date_key (from dim_date)
        #   city_key (from dim_city)
        #   status_key (from dim_status)
        #   TRY_CAST(amount AS DOUBLE) AS amount
        #   TRY_CAST(amount AS DOUBLE) > 50 AS is_high_value
        # WHERE amount IS NOT NULL
        query = """
        INSERT OR REPLACE INTO fact_orders
        SELECT
            id AS order_key,
            dim_date.date_key,
            dim_city.city_key,
            dim_status.status_key,
            TRY_CAST(deliveries.amount AS DOUBLE) AS amount,
            TRY_CAST(deliveries.amount AS DOUBLE) > 50 AS is_high_value
        FROM deliveries
        LEFT JOIN dim_date
        ON deliveries.order_date = dim_date.date
        LEFT JOIN dim_city
        ON deliveries.city = dim_city.city_name
        LEFT JOIN dim_status
        ON deliveries.status = dim_status.status_name
        WHERE deliveries.amount IS NOT NULL
        """
        con.execute(query=query)

        logger.info("fact_orders loaded.")


def query_star(db_path: str) -> None:
    """Total and avg amount per city per status — weekdays only."""

    # TODO: Write a query that joins all 4 tables:
    #   fact_orders → dim_city (on city_key)
    #   fact_orders → dim_status (on status_key)
    #   fact_orders → dim_date (on date_key)
    # Filter: WHERE dim_date.is_weekend = false
    # Group by: city_name, status_name
    # Select: city_name AS city, status_name AS status,
    #         SUM(amount) AS total_amount,
    #         ROUND(AVG(amount), 2) AS avg_amount,
    #         COUNT(*) AS order_count
    # Order by: city, status

    sql = """
        SELECT
            c.city_name AS city,
            s.status_name AS status,
            SUM(f.amount) AS total_amount,
            ROUND(AVG(f.amount), 2) AS avg_amount,
            COUNT(*) AS order_count
        FROM fact_orders AS f
        LEFT JOIN dim_date AS d
        ON f.date_key = d.date_key
        LEFT JOIN dim_city AS c
        ON f.city_key = c.city_key
        LEFT JOIN dim_status AS s
        ON f.status_key = s.status_key
        WHERE d.is_weekend = false
        GROUP BY c.city_name, s.status_name
        ORDER BY c.city_name, s.status_name
    """
    run_query(
        title="Star Query — Weekday orders by city and status",
        query=sql,
        columns=["city", "status", "total_amount",
                 "avg_amount", "order_count"],
    )


if __name__ == "__main__":
    create_star_schema(DB)
    load_dimensions(DB)
    load_facts(DB)
    query_star(DB)
