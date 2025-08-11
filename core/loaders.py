from __future__ import annotations
import pandas as pd
from typing import List
from .schema import normalize_headers
from .transforms import parse_price, parse_percent, parse_int, coerce_numeric, ensure_country_column
from .config import PRICE_COLS, PCT_COLS, INT_COLS

def read_any(path_or_file):
    name = getattr(path_or_file, "name", str(path_or_file)).lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(path_or_file, dtype=str)
    return pd.read_csv(path_or_file, dtype=str)

def load_many(files: List) -> pd.DataFrame:
    frames = []
    for f in files:
        df = read_any(f)
        df = normalize_headers(df)
        df = coerce_numeric(df, PRICE_COLS, parse_price)
        df = coerce_numeric(df, PCT_COLS, parse_percent)
        df = coerce_numeric(df, INT_COLS, parse_int)
        df = ensure_country_column(df)
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    df_all = pd.concat(frames, ignore_index=True)
    if {"asin","country"}.issubset(df_all.columns):
        df_all = df_all.drop_duplicates(subset=["asin","country"])
    return df_all
