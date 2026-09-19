{{ config(materialized='table') }}

WITH data AS (
SELECT
  order_date,
  restaurant_name,
  COUNT(*) AS total_orders,
  SUM(amount) AS total_revenue,
  AVG(amount) AS avg_order_value,
FROM {{ ref('stg_restaurant_orders') }}
GROUP BY restaurant_name, order_date
)
SELECT
  *,
  {{ revenue_tier('total_revenue', 200, 100) }} AS revenue_tier
FROM data
