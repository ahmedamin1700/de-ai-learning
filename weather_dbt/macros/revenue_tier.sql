{% macro revenue_tier(col_name, high_threshold, low_threshold) %}
  CASE
    WHEN {{ col_name }} >= {{ high_threshold }} THEN 'high'
    WHEN {{ col_name }} >= {{ low_threshold }} THEN 'med'
    ELSE 'low'
  END
{% endmacro %}
