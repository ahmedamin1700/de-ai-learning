{{ config(materialized='view') }}

SELECT
  order_id,
  LOWER(restaurant_name) AS restaurant_name,
  LOWER(city) AS city,
  TRY_CAST(amount AS DOUBLE) AS amount,
  status,
  order_date,
  TRY_CAST(amount AS DOUBLE) > 80 AS is_high_value
FROM {{ source('warehouse', 'restaurant_orders_raw') }}
WHERE status = 'delivered'
