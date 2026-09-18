SELECT
  city,
  total_revenue
FROM {{ ref('mart_city_summary')}}
WHERE total_revenue <= 0
