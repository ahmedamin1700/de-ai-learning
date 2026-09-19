SELECT
  restaurant_name,
  restaurant_category,
  SUM(order_total) AS total_orders,
  SUM(order_revenue) AS total_revenue,
  ROUND(AVG(order_total), 2) AS avg_order_value,
  SUM(is_free_delivery) AS free_delivery_count
FROM {{ ref('stg_orders') }}
GROUP BY restaurant_name, restaurant_category
