import requests
import time
import logging

from src.io.file_ops import write_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch(url: str, params: dict, retries: int = 3) -> dict:
    attempts = 0

    while attempts <= retries:
        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 429:
                attempts += 1
                if attempts <= retries:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(
                        f"Rate limited (429) on {url}. "
                        f"Waiting {retry_after} seconds before retrying."
                    )
                    time.sleep(retry_after)
                else:
                    break
            elif 500 <= response.status_code < 600:
                attempts += 1
                if attempts <= retries:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(
                        f"Server error ({response.status_code}) on {url}. "
                        f"Attempt {attempts}/{retries}. "
                        f"Retrying in {retry_after} seconds."
                    )
                    time.sleep(retry_after)
                else:
                    break
            elif 400 <= response.status_code < 500:
                raise ValueError(
                    f"Client error ({response.status_code}) occurred. "
                    f"Retrying will not help. Response text: {response.text}"
                )
        except requests.exceptions.Timeout:
            attempts += 1
            if attempts <= retries:
                logger.warning(
                    f"Request timed out on {url}. "
                    f"Attempt {attempts}/{retries}. Retrying in 5 seconds."
                )
                time.sleep(5)
            else:
                break

    raise RuntimeError(
        f"Failed to fetch data from {url} "
        f"after exhausting {retries} retries due to persistent errors."
    )


def get_weather(lat: float, lon: float, days: int = 3) -> list[dict]:
    url = "https://api.open-meteo.com/v1/forecast"
    query_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "forecast_days": days
    }

    res = fetch(url, params=query_params)
    logger.info("Successfully fetched weather data.")

    times = res["hourly"]["time"]
    temperatures = res["hourly"]["temperature_2m"]
    return [
        {
            "time": time,
            "temperature_c": temperature
        }
        for time, temperature in zip(times, temperatures)
    ]


def fetch_cities(cities: list[dict]) -> list[dict]:
    results = []
    for city in cities:
        data = get_weather(city["lat"], city["lon"])
        for record in data:
            record["city"] = city["name"]
            results.append(record)
    return results


def main():
    cities = [
        {"name": "Cairo", "lat": 30.06, "lon": 31.24},
        {"name": "Dubai", "lat": 25.20, "lon": 55.27},
        {"name": "Alexandria", "lat": 31.20, "lon": 29.92},
        {"name": "Riyadh", "lat": 24.69, "lon": 46.72},
        {"name": "Kuwait City", "lat": 29.37, "lon": 47.98},
        {"name": "Amman", "lat": 31.95, "lon": 35.93},
        {"name": "Beirut", "lat": 33.89, "lon": 35.50},
    ]
    result = fetch_cities(cities)
    write_json(result, "data/raw/weather.json")


# Executing the script
if __name__ == "__main__":
    main()
