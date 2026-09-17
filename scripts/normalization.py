import duckdb
import logging
from rich.console import Console
from rich.table import Table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

DB = "data/warehouse.db"

# NORMALIZATION VIOLATIONS IN raw_orders
# =======================================
# Table: order_id | customer_name | customer_email | customer_city |
#        customer_region | product_name | product_category | product_price |
#        quantity | order_date
#
# Violation 1:
#   Columns: customer_name, customer_email, customer_city
#   Violates: 3NF (Third Normal Form)
#   Why: These columns describe the customer, not the order. They depend on
#        the customer identity, not on order_id. If the same customer places
#        100 orders, their name and email are repeated 100 times. One email
#        change requires 100 row updates — a transitive dependency.
#   Should move to: dim_customers (customer_id PK, name, email, city)
#
# Violation 2:
#   Columns: product_name, product_category, product_price
#   Violates: 3NF (Third Normal Form)
#   Why: These describe the product, not the order event. If a product's price
#        changes, every historical order row must be updated. They transitively
#        depend on an implicit product identity, not on order_id.
#   Should move to: dim_products (product_id PK, name, category, unit_price)
#
# Violation 3:
#   Columns: customer_region
#   Violates: 3NF (Third Normal Form) — transitive dependency
#   Why: customer_region depends on customer_city, which depends on order_id.
#        The chain is: order_id → customer_city → customer_region.
#        A non-key column (region) depends on another non-key column (city),
#        not directly on the primary key. Changing a city's region requires
#        updating every order row for that city.
#   Should move to: dim_cities (city_id PK, city_name, region)


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


def create_normalized_schema(db_path: str) -> None:
    """Create new normalized dimension tables (don't touch existing fact_orders)."""
    with duckdb.connect(db_path) as con:

        # TODO: CREATE TABLE IF NOT EXISTS dim_customers
        # Columns: customer_id INTEGER PRIMARY KEY, name VARCHAR, email VARCHAR
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS dim_customers (
                customer_id INTEGER PRIMARY KEY,
                name VARCHAR,
                email VARCHAR
            )
            """
        )
        logger.info("dim_customers table created.")

        # TODO: CREATE TABLE IF NOT EXISTS dim_products
        # Columns: product_id INTEGER PRIMARY KEY, name VARCHAR,
        #          category VARCHAR, unit_price DOUBLE
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS dim_products (
                product_id INTEGER PRIMARY KEY,
                name VARCHAR,
                category VARCHAR,
                unit_price DOUBLE
            )
            """
        )
        logger.info("dim_products table created.")

        # TODO: CREATE TABLE IF NOT EXISTS dim_cities
        # Columns: city_id INTEGER PRIMARY KEY, city_name VARCHAR, region VARCHAR
        # Note: this is DIFFERENT from dim_city (which has no region)
        # Add region as extra attribute — this is what 3NF would give you
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS dim_cities (
                city_id INTEGER PRIMARY KEY,
                city_name VARCHAR,
                region VARCHAR
            )
            """
        )
        logger.info("dim_cities table created.")

        logger.info("Normalized schema tables created.")


def create_wide_view(db_path: str) -> None:
    """Create a denormalized wide view over the existing star schema."""
    with duckdb.connect(db_path) as con:

        # TODO: CREATE OR REPLACE VIEW wide_orders AS
        # JOIN fact_orders with dim_city, dim_date, dim_status
        # Select: order_key, amount, is_high_value,
        #         city_name, day_of_week, month_name, is_weekend, status_name
        con.execute(
            """
            CREATE OR REPLACE VIEW wide_orders AS
            SELECT
                order_key,
                amount,
                is_high_value,
                city_name,
                day_of_week,
                month_name,
                is_weekend,
                status_name
            FROM fact_orders AS f
            LEFT JOIN dim_date AS d
                ON f.date_key = d.date_key
            LEFT JOIN dim_city AS c
                ON f.city_key = c.city_key
            LEFT JOIN dim_status AS s
                ON f.status_key = s.status_key
            """
        )
        logger.info("wide_orders view created.")


def query_normalized(db_path: str) -> None:
    """Total amount per city for delivered orders — using star schema joins."""
    sql = """
        -- TODO: Join fact_orders → dim_city → dim_status
        -- Filter: status_name = 'delivered'
        -- Group by: city_name
        -- Select: city_name, SUM(amount) AS total_amount
        -- Order by: total_amount DESC
        SELECT
            city_name,
            SUM(amount) AS total_amount
            FROM fact_orders AS f
            LEFT JOIN dim_date AS d
                ON f.date_key = d.date_key
            LEFT JOIN dim_city AS c
                ON f.city_key = c.city_key
            LEFT JOIN dim_status AS s
                ON f.status_key = s.status_key
            WHERE s.status_name = 'delivered'
            GROUP BY city_name,
            ORDER BY SUM(amount) DESC
    """
    run_query(
        title="Normalized Query — Delivered total per city",
        query=sql,
        columns=["city", "total_amount"],
    )


def query_denormalized(db_path: str) -> None:
    """Total amount per city for delivered orders — using wide_orders view."""
    sql = """
        -- TODO: SELECT from wide_orders (no joins needed)
        -- Filter: status_name = 'delivered'
        -- Group by: city_name
        -- Select: city_name, SUM(amount) AS total_amount
        -- Order by: total_amount DESC
        SELECT
            city_name,
            SUM(amount) AS total_amount
        FROM wide_orders
        WHERE status_name = 'delivered'
        GROUP BY city_name,
        ORDER BY SUM(amount) DESC
    """
    run_query(
        title="Denormalized Query — Delivered total per city (wide view)",
        query=sql,
        columns=["city", "total_amount"],
    )


# TRADE-OFF SUMMARY
# =================
# Normalized (star schema):
#   Pros: Single source of truth — update one place, all queries reflect it.
#         No data redundancy, smaller storage footprint.
#         Enforces data integrity — no risk of inconsistent values.
#   Cons: Queries require multiple joins — more complex and slower on large data.
#         Harder for non-technical analysts to write queries directly.
#   Use when: Source/transactional systems, data that changes frequently,
#             anywhere correctness and consistency matter more than read speed.
#
# Denormalized (wide view / flat table):
#   Pros: Single table scan — no joins, fast for BI tools and dashboards.
#         Simple queries — analysts can SELECT without knowing the schema.
#         Better performance on read-heavy analytical workloads.
#   Cons: Data is duplicated — storage cost is higher.
#         Updates must touch many rows — risk of inconsistency if not managed.
#         Stale data if source changes and the flat table isn't refreshed.
#   Use when: Analytics, reporting, dashboards — read-heavy, updated in batch,
#             downstream of a normalized source of truth.


if __name__ == "__main__":
    create_normalized_schema(DB)
    create_wide_view(DB)
    query_normalized(DB)
    query_denormalized(DB)
