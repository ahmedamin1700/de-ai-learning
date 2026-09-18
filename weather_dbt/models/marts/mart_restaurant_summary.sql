-- - Source: {{ ref('int_orders_by_restaurant') }}
-- - Join with {{ ref('stg_orders') }} to also get city breakdown — actually, keep it simple: just SELECT everything from int_orders_by_restaurant, ordered by total_revenue DESC
-- - Materialized as table
-- - Tests in schema.yml: restaurant_name unique + not_null, total_revenue not_null

SELECT
  r.*,
  {{ revenue_tier('total_revenue', 100, 50) }} AS revenue_tier   
FROM {{ ref('int_orders_by_restaurant') }} AS r
-- LEFT JOIN {{ ref('stg_orders') }} AS o
--   ON r.restaurant_name = o.restaurant_name
ORDER BY r.total_revenue DESC

