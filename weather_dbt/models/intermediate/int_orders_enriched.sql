{{ config(materialized='view') }}

WITH deliveries AS (
  SELECT * FROM {{ ref('stg_deliveries')}}
),
weather AS (
  SELECT * FROM {{ ref('stg_weather')}}
)
SELECT
  d.delivery_id,
  d.city,
  d.status,
  d.amount,
  d.is_high_value, 
  d.order_date, 
  w.avg_temp, 
  ROUND(d.amount / NULLIF(w.avg_temp, 0), 2) AS revenue_per_degree
FROM deliveries AS d
LEFT JOIN weather AS w
  ON d.city = w.city
