SELECT
  id AS delivery_id,
  TRIM(LOWER(city)) AS city,
  TRIM(LOWER(status)) AS status,
  TRY_CAST(amount AS DOUBLE) AS amount,
  TRY_CAST(amount AS DOUBLE) > {{ var('high_value_threshold') }} AS is_high_value,
  CAST(order_date AS DATE) AS order_date,
  {{ cents_to_dollars('TRY_CAST(amount AS DOUBLE)') }} AS amount_usd,
  {{ classify_order('amount', 100, 50) }} AS order_tier
FROM deliveries
WHERE TRY_CAST(amount AS DOUBLE) IS NOT NULL
AND TRIM(city) != ''
AND city IS NOT NULL
