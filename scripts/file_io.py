import yaml
import csv
import json
from pathlib import Path
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log"),
    ]
)

logger = logging.getLogger(__name__)


def load_config(filepath: str) -> dict:
    file_path = Path(filepath)
    if not file_path.is_file():
        raise FileNotFoundError(
            f"Required config file missing at {file_path}."
        )

    with open(filepath, "r") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, (dict)):
        raise ValueError("Config file is not a dict format.")
    return config


def read_csv(filepath: str) -> list[dict]:
    cleaned_data = []
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for index, row in enumerate(reader):
            cleaned_row = {
                key: (None if val.strip() == "" else val)
                for key, val in row.items()
            }
            cleaned_data.append(cleaned_row)

    return cleaned_data


def write_json(data: list[dict], filepath: str) -> None:
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"{len(data)} added to the file: {filepath}")


def run_pipeline(config_path: str):
    config = load_config(config_path)
    data = read_csv(config["paths"]["raw_input"])

    valid = []
    failed = []

    required_fields = config["processing"]["required_fields"]
    skip_null_amount = config["processing"]["skip_null_amount"]
    for row in data:
        if any(
            row.get(field) is None for field in required_fields
        ) or (
                skip_null_amount and row.get("amount") is None
        ):
            failed.append(row)
        else:
            valid.append(row)

    valid_path = config["paths"]["processed_output"]
    failed_path = config["paths"]["failed_output"]

    write_json(valid, valid_path)
    write_json(failed, failed_path)

    logger.info(f"Total rows: {len(data)}")
    logger.info(f"Total valid: {len(valid)}")
    logger.info(f"Total failed: {len(failed)}")


if __name__ == "__main__":
    run_pipeline("config/pipeline.yaml")
