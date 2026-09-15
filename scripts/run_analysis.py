import pandas as pd
from src.utils.dataframe_ops import (
    clean_orders, aggregate_weather, enrich_orders
)

if __name__ == "__main__":
    df_orders = pd.read_csv("data/raw/orders.csv")
    df_weather = pd.read_json("data/raw/weather.json")

    df_orders = clean_orders(df_orders)
    df_weather = aggregate_weather(df_weather)

    df = enrich_orders(df_orders, df_weather)
    print(df)
    df.to_csv("data/processed/orders_enriched.csv", index=False)
