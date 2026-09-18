-- - Source: {{ source('seeds', 'raw_orders') }}
-- - Clean and cast: 
--  order_id (integer),
--  customer_city (lowercase trim),
--  restaurant_name (lowercase trim),
--  restaurant_category (lowercase trim),
--  order_total (DOUBLE),
--  delivery_fee (DOUBLE),
--  order_status (lowercase trim)
--
-- - Cast ordered_at to TIMESTAMP
-- - Add order_revenue = order_total - delivery_fee
-- - Add is_free_delivery = boolean where delivery_fee = 0
-- - Filter out nulls and cancelled orders in WHERE: keep only delivered
-- - Tests in schema.yml: order_id unique + not_null, order_status accepted_values ['delivered'], order_total not_null

SELECT
  TRY_CAST(order_id AS INTEGER) AS order_id,
  TRIM(LOWER(customer_city)) AS customer_city,
  TRIM(LOWER(restaurant_name)) AS restaurant_name,
  TRIM(LOWER(restaurant_category)) AS restaurant_category,
  TRY_CAST(order_total AS DOUBLE) AS order_total,
  TRY_CAST(delivery_fee AS DOUBLE) AS delivery_fee,
  TRIM(LOWER(order_status)) AS order_status,
  TRY_CAST(ordered_at AS TIMESTAMP) AS ordered_at,
  TRY_CAST(order_total AS DOUBLE) - TRY_CAST(delivery_fee AS DOUBLE) AS order_revenue,
  TRY_CAST(delivery_fee AS DOUBLE) = 0 AS is_free_delivery
FROM {{ source('seeds', 'raw_orders')}}
WHERE TRIM(LOWER(order_status)) = 'delivered'
