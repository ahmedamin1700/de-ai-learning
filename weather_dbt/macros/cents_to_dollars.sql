{% macro cents_to_dollars(column_name)%}
  ROUND({{column_name}} / 100.0, 2)
{% endmacro%}
