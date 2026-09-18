{% macro classify_order(amount_col, high_threshold, low_threshold) %}
    CASE
        WHEN {{ amount_col }} >= {{ high_threshold }} THEN 'high'
        WHEN {{ amount_col }} >= {{ low_threshold }} THEN 'medium'
        ELSE 'low'
    END
{% endmacro %}
