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


def query_6() -> None:
    """Multi-step CTE: delivered revenue by city, flag if exceeds 100."""
    sql = """
        -- TODO: Step 1 — CTE 'delivered': filter WHERE status = 'delivered'
        -- TODO: Step 2 — CTE 'city_revenue': SUM(amount) per city from delivered
        -- TODO: Step 3 — SELECT city, revenue, revenue > 100 AS exceeds_100
        -- No subqueries allowed — CTEs only
        WITH delivered AS (
            SELECT * FROM deliveries WHERE status = 'delivered'
        ),
        city_revenue AS (
            SELECT city, SUM(amount) AS revenue from delivered
            GROUP BY city
        )
        SELECT city, revenue, revenue > 100 AS exceeds_100 FROM city_revenue;
    """
    run_query(
        title="Query 6 — Delivered revenue by city",
        query=sql,
        columns=["city", "revenue", "exceeds_100"],
    )


def query_7() -> None:
    """Three-step CTE: top order per city vs city average."""
    sql = """
        -- TODO: CTE 'ranked'    — add RANK() OVER (PARTITION BY city ORDER BY amount DESC)
        -- TODO: CTE 'top_orders' — filter WHERE rank = 1
        -- TODO: CTE 'city_avgs'  — compute AVG(amount) per city from deliveries
        -- TODO: Final SELECT — join top_orders with city_avgs
        -- Expected columns: city, top_amount, city_avg, diff (top_amount - city_avg, rounded 2dp)
        WITH ranked AS (
            SELECT *, RANK() OVER (PARTITION BY city ORDER BY amount DESC) AS rank
            FROM deliveries
        ),
        top_orders AS (
            SELECT * FROM ranked WHERE rank = 1
        ),
        city_avgs AS (
            SELECT city, AVG(amount) AS city_avg FROM deliveries GROUP BY city
        )
        SELECT
            t.city,
            t.amount AS top_amount,
            ROUND(c.city_avg, 2) AS city_avg,
            ROUND(t.amount - c.city_avg, 2) AS diff
        FROM top_orders AS t
        LEFT JOIN city_avgs AS c
            ON t.city = c.city
    """
    run_query(
        title="Query 7 — Top order vs city average",
        query=sql,
        columns=["city", "top_amount", "city_avg", "diff"],
    )


def query_8() -> None:
    """Recursive CTE: date series joined with deliveries."""
    sql = """
        -- TODO: Recursive CTE 'date_series'
        --   Base case:    SELECT DATE '2026-09-01' AS date
        --   Recursive:    SELECT date + INTERVAL '1 day' FROM date_series WHERE date < DATE '2026-09-07'
        -- TODO: Left join date_series with deliveries on date = order_date
        -- TODO: SUM(amount) per date, use COALESCE(..., 0) so missing days show 0
        -- Expected columns: date, total_amount
        WITH RECURSIVE date_series AS (
            SELECT DATE '2026-09-01' AS date
            UNION ALL
            SELECT date + INTERVAL 1 DAY FROM date_series
            WHERE date < DATE '2026-09-07'
        )
        SELECT
            dates.date,
            COALESCE(SUM(d.amount), 0) AS total_amount
        FROM date_series AS dates
        LEFT JOIN deliveries AS d
        ON dates.date = d.order_date
        GROUP BY 1
        ORDER BY 1
    """
    run_query(
        title="Query 8 — Daily totals with date series",
        query=sql,
        columns=["date", "total_amount"],
    )


def query_9() -> None:
    """Rewrite a correlated subquery using a CTE."""
    # Original slow query (correlated subquery — runs once per row):
    # SELECT *
    # FROM deliveries d1
    # WHERE d1.amount > (
    #     SELECT AVG(d2.amount)
    #     FROM deliveries d2
    #     WHERE d2.city = d1.city
    # )
    # ORDER BY d1.city, d1.amount DESC;

    sql = """
        -- TODO: CTE 'city_avgs' — compute AVG(amount) per city once
        -- TODO: JOIN deliveries with city_avgs on city
        -- TODO: Filter WHERE amount > city_avg
        -- TODO: SELECT only: id, city, amount, status, city_avg (rounded 2dp)
        -- TODO: ORDER BY city, amount DESC

        -- After writing the query, run EXPLAIN on both versions in a separate
        -- duckdb.connect() block below and add a comment here about what you observe.
        WITH city_avgs AS (
            SELECT city, AVG(amount) AS city_avg
            FROM deliveries
            GROUP BY city
        )
        SELECT
            d.id,
            d.city,
            d.amount,
            d.status,
            ROUND(c.city_avg, 2) AS city_avg
        FROM deliveries AS d
        LEFT JOIN city_avgs AS c
        ON d.city = c.city
        WHERE d.amount > c.city_avg
    """
    run_query(
        title="Query 9 — Optimized: above-average orders per city",
        query=sql,
        columns=["id", "city", "amount", "status", "city_avg"],
    )


if __name__ == "__main__":
    seed_data()
    query_1()
    query_2()
    query_3()
    query_4()
    query_5()
    query_6()
    query_7()
    query_8()
    query_9()
