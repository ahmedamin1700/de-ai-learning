WITH deliveries AS (
    SELECT * FROM {{ ref('stg_deliveries') }}
),

weather AS (
    SELECT * FROM {{ ref('stg_weather') }}
),

city_orders AS (
    SELECT
        city,
        COUNT(*)                                        AS total_orders,
        SUM(amount)                                     AS total_revenue,
        ROUND(AVG(amount), 2)                           AS avg_order_value,
        COUNT(*) FILTER (WHERE status = 'delivered')    AS delivered_count
    FROM deliveries
    GROUP BY city
)

SELECT
    o.city,
    o.total_orders,
    o.total_revenue,
    o.avg_order_value,
    o.delivered_count,
    w.avg_temp,
    w.max_temp,
    w.min_temp
FROM city_orders o
LEFT JOIN weather w ON o.city = w.city
ORDER BY o.total_revenue DESC
