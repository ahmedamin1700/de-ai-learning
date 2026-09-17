SELECT
  id AS delivery_id,
  TRIM(LOWER(city)) AS city,
  TRIM(LOWER(status)) AS status,
  TRY_CAST(amount AS DOUBLE) AS amount,
  TRY_CAST(amount AS DOUBLE) > 50 AS is_high_value,
  CAST(order_date AS DATE) AS order_date
FROM deliveries
WHERE TRY_CAST(amount AS DOUBLE) IS NOT NULL
AND TRIM(city) != ''
AND city IS NOT NULL
