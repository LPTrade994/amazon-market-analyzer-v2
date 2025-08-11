from __future__ import annotations
import re
import pandas as pd
from .config import ALIAS_MAP

def normalize_header(h: str) -> str:
    if not isinstance(h, str):
        return h
    t = h.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return ALIAS_MAP.get(t, t.replace(" ", "_"))

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_header(c) for c in df.columns]
    return df

def required_columns_present(df: pd.DataFrame, required: list[str]) -> tuple[bool, list[str]]:
    cols = set(df.columns)
    missing = [c for c in required if c not in cols]
    return (len(missing) == 0, missing)
