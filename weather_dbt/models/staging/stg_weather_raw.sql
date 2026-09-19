{{ config(materialized='view') }}

SELECT
    TRIM(LOWER(city))           AS city,
    TRY_CAST(time AS TIMESTAMP) AS recorded_at,
    temperature_c
FROM {{ source('warehouse', 'weather_raw') }}
WHERE temperature_c IS NOT NULL
