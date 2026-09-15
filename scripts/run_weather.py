from src.pipeline import WeatherPipeline

CITIES = [
    {"name": "Cairo", "lat": 30.06, "lon": 31.24},
    {"name": "Dubai", "lat": 25.20, "lon": 55.27},
    {"name": "Alexandria", "lat": 31.20, "lon": 29.92},
    {"name": "Riyadh", "lat": 24.69, "lon": 46.72},
]

if __name__ == "__main__":
    pipeline = WeatherPipeline(CITIES, days=2)
    pipeline.run()
    pipeline.save("data/raw/weather_oop.json")
