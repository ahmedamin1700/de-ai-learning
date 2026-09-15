import re
from collections import Counter


def clean_string(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def clean_price(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    cleaned = cleaned.replace(",", "")
    if not cleaned:
        return None
    match = re.search(r"[-+]?\d*\.\d+|\d+", cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def normalize_list(values: list, func) -> list:
    return [func(item) for item in values]


def summarize(data: list[dict], key: str) -> dict:
    target = [item[key] for item in data]

    valid_values = [v for v in target if v is not None]
    if valid_values:
        most_common_val = Counter(valid_values).most_common(1)[0][0]
    else:
        most_common_val = None

    return {
        "count": len(target),
        "unique_count": len(set(valid_values)),
        "most_common": most_common_val,
        "nulls": target.count(None)
    }
