SELECT
  delivery_id,
  amount
FROM {{ ref('stg_deliveries')}}
WHERE amount < 0
AND status = 'delivered'
