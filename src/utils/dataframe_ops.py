import numpy as np
import pandas as pd


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["city"] = df["city"].str.strip().str.lower()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["city"] = df["city"].replace("", np.nan)
    df = df.dropna(subset=["amount", "city"])
    df["is_high_value"] = df["amount"] > 50
    return df


def aggregate_weather(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["city"] = df["city"].str.strip().str.lower()
    df_grouped = df.groupby("city").agg(
        avg_temp=("temperature_c", "mean"),
        max_temp=("temperature_c", "max"),
        min_temp=("temperature_c", "min"),
        record_count=("temperature_c", "count")
    ).reset_index()

    df_grouped["avg_temp"] = df_grouped["avg_temp"].round(1)
    return df_grouped


def enrich_orders(
        orders_df: pd.DataFrame, weather_summary_df: pd.DataFrame
) -> pd.DataFrame:
    df_orders = orders_df.copy()
    df_weather = weather_summary_df.copy()

    df_merged = pd.merge(df_orders, df_weather, on="city", how="left")
    return df_merged
