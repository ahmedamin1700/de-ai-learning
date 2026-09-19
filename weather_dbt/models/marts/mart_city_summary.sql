WITH orders AS (
    SELECT * FROM {{ ref('int_orders_enriched') }}
)

SELECT
    city,
    COUNT(*)                                        AS total_orders,
    SUM(amount)                                     AS total_revenue,
    ROUND(AVG(amount), 2)                           AS avg_order_value,
    COUNT(*) FILTER (WHERE status = 'delivered')    AS delivered_count,
    ROUND(AVG(avg_temp), 1)                         AS avg_temp,
    ROUND(AVG(revenue_per_degree), 4)               AS avg_revenue_per_degree
FROM orders
GROUP BY city
ORDER BY total_revenue DESC
