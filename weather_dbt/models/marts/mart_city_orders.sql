SELECT
  customer_city,
  SUM(order_total) AS total_orders,
  SUM(order_revenue) AS total_revenue,
  AVG(order_total) AS avg_order_value,
  COUNT(DISTINCT restaurant_name) AS unique_restaurants
FROM {{ ref('stg_orders') }}
GROUP BY customer_city
ORDER BY SUM(order_revenue) DESC
