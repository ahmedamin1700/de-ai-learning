import logging
from dataclasses import dataclass, asdict
from weather_api import get_weather
from file_io import write_json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CityRecord:
    city: str
    time: str
    temperature_c: float

    def to_dict(self) -> dict:
        return asdict(self)


class WeatherPipeline:
    def __init__(self, cities: list[dict], days: int = 3) -> None:
        self.cities = cities
        self.days = days
        self.records: list[CityRecord] = []
        self.failed_cities: list[str] = []

    def _fetch_city(self, city: dict) -> list[CityRecord]:
        lat = city["lat"]
        lon = city["lon"]

        name = city["name"]
        try:
            records = get_weather(lat, lon, self.days)
            return [
                CityRecord(
                    city=name, time=r["time"], temperature_c=r["temperature_c"]
                )
                for r in records
            ]
        except Exception as e:
            logger.error(f"Failed to fetch city: {name} with {e}")
            self.failed_cities.append(name)
            return []

    def run(self) -> None:
        logger.info(f"Starting pipeline for {len(self.cities)} cities")

        for city in self.cities:
            result = self._fetch_city(city)

            if result:
                self.records.extend(result)
                logger.info(f"{city["name"]}: {len(result)} records fetched")

        logger.info(f"Total records: {len(self.records)}")
        logger.info(f"Total failed cities: {len(self.failed_cities)}")

    def save(self, filepath: str) -> None:
        if not self.records:
            raise RuntimeError("No records to save. Call run() before save().")
        data = [record.to_dict() for record in self.records]
        write_json(data, filepath)


if __name__ == "__main__":
    cities = [
        {"name": "Cairo", "lat": 30.06, "lon": 31.24},
        {"name": "Dubai", "lat": 25.20, "lon": 55.27},
        {"name": "Alexandria", "lat": 31.20, "lon": 29.92},
        {"name": "Riyadh", "lat": 24.69, "lon": 46.72},
    ]
    pipeline = WeatherPipeline(cities, days=2)
    pipeline.run()
    pipeline.save("data/raw/weather_oop.json")
