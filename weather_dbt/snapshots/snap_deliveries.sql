{% snapshot snap_deliveries %}
{{
  config(
    target_schema='main',
    unique_key='id',
    strategy='check',
    check_cols=['status', 'amount'],
  )
}}
SELECT
  id,
  city,
  status,
  amount,
  order_date
FROM {{ source('warehouse', 'deliveries') }}
{% endsnapshot %}
