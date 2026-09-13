from pathlib import Path
import json
import logging

from utils import clean_price, clean_string

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log"),
    ]
)

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    pass


def load_orders(filepath: str) -> list[dict]:
    # Get the directory of the current script and build the path
    file_path = Path(filepath)

    # Check if the file exists
    if not file_path.is_file():
        raise FileNotFoundError(f"Required JSON file missing: {file_path}")

    # Read the file and validate its content
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError(f"The file is not a valid JSON document: {e}")

    # 4. Enforce that the JSON root is a list
    if not isinstance(data, list):
        raise ValueError(
            f"Invalid JSON structure at {file_path.name}: "
            f"Expected a list, but got {type(data).__name__}."
        )

    return data


def process_order(order: dict) -> dict | None:
    required_keys = {"id", "city", "amount", "status"}

    missing_keys = required_keys - order.keys()
    if missing_keys:
        missing_str = ", ".join(sorted(missing_keys))
        raise DataValidationError(
            f"Missing required keys: {missing_str}"
        )

    cleaned_price = clean_price(order["amount"])
    if not cleaned_price:
        logger.warning("This order has a None order amount.")
        return None

    return {
        **order,
        "city": clean_string(order["city"]),
        "amount": cleaned_price
    }


def process_all(orders: list[dict]) -> list[dict]:
    result = []
    for index, order in enumerate(orders):
        try:
            processed_order = process_order(order)
            if processed_order:
                result.append(processed_order)
        except DataValidationError as e:
            logger.error(f"Error at order with index: {index} with {e}")
    return result


def main():
    logger.info("Pipeline started.")
    orders = load_orders("data/raw/orders.json")
    processed = process_all(orders)
    logger.info(
        f"Success rows: {len(processed)} "
        f"Failed rows: {len(orders) - len(processed)}"
    )
    with open("data/processed/orders_clean.json", "w") as file:
        json.dump(processed, file, indent=4)

    logger.info("Pipeline finished.")


if __name__ == "__main__":
    main()
