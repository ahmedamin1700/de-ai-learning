import argparse
import sys
import pandas as pd
from rich.console import Console
from rich.table import Table

from src.io.file_ops import load_config
from src.pipeline.weather_pipeline import WeatherPipeline
from src.utils.dataframe_ops import aggregate_weather

console = Console()

MAX_DAYS = 7


def parse_args():
    parser = argparse.ArgumentParser(description="Weather Intelligence CLI")
    parser.add_argument("--cities", nargs="+", required=True)
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--output", default="weather_report.csv")
    return parser.parse_args()


def load_cities(config_path: str) -> dict:
    config = load_config(config_path)
    return config["cities"]


def resolve_cities(requested: list[str], city_registry: dict) -> list[dict]:
    result = []
    for city in requested:
        if city.lower() in city_registry:
            result.append(
                {
                    "name": city.lower(),
                    "lat": city_registry[city.lower()]["lat"],
                    "lon": city_registry[city.lower()]["lon"],
                }
            )
        else:
            console.print(f"[red] This city {
                city} not found in the registry.[/red]")
            continue
    return result


def validate_days(days: int) -> None:
    if days < 1 or days > MAX_DAYS:
        console.print(
            f"[red] Days must fall in that range [1, {MAX_DAYS}][/red]")
        sys.exit(1)


def print_table(summary_df: pd.DataFrame) -> None:
    table = Table()
    table.add_column("city")
    table.add_column("avg_temp")
    table.add_column("max_temp")
    table.add_column("min_temp")
    table.add_column("record_count")

    for city, avg_temp, max_temp, min_temp, record_count in summary_df.itertuples(
        index=False
    ):
        table.add_row(
            str(city),
            str(avg_temp),
            str(max_temp),
            str(min_temp),
            str(record_count),
        )
    console.print(table)


def main():
    args = parse_args()

    validate_days(args.days)

    city_registry = load_cities("config/cities.yaml")
    cities = resolve_cities(args.cities, city_registry)

    if not cities:
        console.print("[red]No valid cities found. Exiting.[/red]")
        sys.exit(1)

    console.print("\n🌍 [bold]Weather Intelligence CLI[/bold]")
    console.print(
        f"Fetching weather for {len(cities)} cities over {args.days} days...\n"
    )

    weather = WeatherPipeline(cities, args.days)
    weather.run()

    if not weather.records:
        console.print("[red]Error no records found.[/red]")
        sys.exit(1)

    df = pd.DataFrame([record.to_dict() for record in weather.records])
    df_aggregated = aggregate_weather(df)
    print_table(df_aggregated)
    df_aggregated.to_csv(args.output, index=False)
    console.print(f"[green]💾 Report saved to: {args.output}[/green]")


if __name__ == "__main__":
    main()
