import duckdb
from rich.console import Console
from rich.table import Table

console = Console()
DB = "data/warehouse.db"


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


def seed_data() -> None:
    """Create and populate the deliveries table."""
    with duckdb.connect(DB) as con:
        con.execute("""
            CREATE OR REPLACE TABLE deliveries AS
            SELECT * FROM (VALUES
                (1,  'cairo',      'delivered',  45.50,  '2026-09-01'),
                (2,  'cairo',      'cancelled',  30.00,  '2026-09-02'),
                (3,  'cairo',      'delivered',  80.00,  '2026-09-03'),
                (4,  'dubai',      'delivered',  120.00, '2026-09-01'),
                (5,  'dubai',      'delivered',  95.00,  '2026-09-02'),
                (6,  'dubai',      'cancelled',  60.00,  '2026-09-03'),
                (7,  'alexandria', 'delivered',  30.00,  '2026-09-01'),
                (8,  'alexandria', 'delivered',  55.00,  '2026-09-02'),
                (9,  'alexandria', 'cancelled',  20.00,  '2026-09-03'),
                (10, 'riyadh',     'delivered',  200.00, '2026-09-01'),
                (11, 'riyadh',     'delivered',  150.00, '2026-09-02'),
                (12, 'riyadh',     'cancelled',  75.00,  '2026-09-03')
            ) t(id, city, status, amount, order_date)
        """)
    console.print("[green]✅ deliveries table seeded[/green]\n")


def query_1() -> None:
    """Rank orders by amount within each city (highest = rank 1)."""
    sql = """
        -- TODO: write your query here
        -- Use ROW_NUMBER() or RANK() OVER (PARTITION BY city ORDER BY amount DESC)
        -- Expected columns: id, city, amount, rank_in_city
        SELECT
            id,
            city,
            amount,
            ROW_NUMBER() OVER(PARTITION BY city ORDER BY amount DESC) AS rank_in_city
        FROM deliveries;
    """
    run_query(
        title="Query 1 — Rank by amount within city",
        query=sql,
        columns=["id", "city", "amount", "rank_in_city"],
    )


def query_2() -> None:
    """Running total of amount per city ordered by date."""
    sql = """
        -- TODO: write your query here
        -- Use SUM(amount) OVER (PARTITION BY city ORDER BY order_date ...)
        -- Expected columns: id, city, order_date, amount, running_total
        SELECT
            id,
            city,
            order_date,
            amount,
            SUM(amount) OVER (PARTITION BY city ORDER BY order_date) AS running_total
        FROM deliveries;
    """
    run_query(
        title="Query 2 — Running total per city",
        query=sql,
        columns=["id", "city", "order_date", "amount", "running_total"],
    )


def query_3() -> None:
    """Each order vs city average amount."""
    sql = """
        -- TODO: write your query here
        -- Use AVG(amount) OVER (PARTITION BY city)
        -- Round city_avg and diff_from_avg to 2 decimal places
        -- Expected columns: id, city, amount, city_avg, diff_from_avg
        SELECT
            id,
            city,
            amount,
            ROUND(AVG(amount) OVER (PARTITION BY city), 2) AS city_avg,
            ROUND(amount - AVG(amount) OVER (PARTITION BY city), 2) AS diff_from_avg
        FROM deliveries;

    """
    run_query(
        title="Query 3 — Order vs city average",
        query=sql,
        columns=["id", "city", "amount", "city_avg", "diff_from_avg"],
    )


def query_4() -> None:
    """Day-over-day amount change per city."""
    sql = """
        -- TODO: write your query here
        -- Use LAG(amount, 1) OVER (PARTITION BY city ORDER BY order_date)
        -- day_change = amount - prev_amount
        -- Expected columns: city, order_date, amount, prev_amount, day_change
        WITH lagged AS (
            SELECT
                city,
                order_date,
                amount,
                LAG(amount, 1) OVER (PARTITION BY city ORDER BY order_date) AS prev_amount
            FROM deliveries
        )
        SELECT
            *,
            amount - prev_amount AS day_change
        FROM lagged;
    """
    run_query(
        title="Query 4 — Day-over-day change per city",
        query=sql,
        columns=["city", "order_date", "amount", "prev_amount", "day_change"],
    )


def query_5() -> None:
    """Top 1 order per city by amount — using window function + CTE."""
    sql = """
        -- TODO: write your query here
        -- Step 1: CTE that adds RANK() OVER (PARTITION BY city ORDER BY amount DESC)
        -- Step 2: SELECT from CTE WHERE rank = 1
        -- Expected columns: id, city, amount, status
        WITH rnk AS (
            SELECT
                *,
                RANK() OVER (PARTITION BY city ORDER BY amount DESC) AS rank
            FROM deliveries
        )
        SELECT
            id,
            city,
            amount,
            status
        FROM rnk
        WHERE rank = 1;
    """
    run_query(
        title="Query 5 — Top order per city",
        query=sql,
        columns=["id", "city", "amount", "status"],
    )


if __name__ == "__main__":
    seed_data()
    query_1()
    query_2()
    query_3()
    query_4()
    query_5()
