SELECT
    TRIM(LOWER(city))       AS city,
    avg_temp,
    max_temp,
    min_temp,
    record_count
FROM weather_summary
