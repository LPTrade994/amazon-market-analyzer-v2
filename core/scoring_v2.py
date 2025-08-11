from __future__ import annotations
import numpy as np
import pandas as pd
from .features import add_all_component_scores
from .config import WEIGHTS

def add_margin_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    th = 0.15
    k = 8.0
    m = df.get("margin_pct", pd.Series([0]*len(df))).fillna(0.0)
    df["score_margin"] = 1/(1 + np.exp(-k*(m - th)))
    return df

def add_opportunity_score(df: pd.DataFrame, weights: dict | None = None) -> pd.DataFrame:
    w = {**WEIGHTS, **(weights or {})}
    df = add_all_component_scores(df)
    df = add_margin_score(df)
    df["opportunity_score_v2"] = (
        w["margin"]*df["score_margin"]
      + w["demand"]*df["score_demand"]
      + w["competition"]*df["score_competition"]
      + w["availability"]*df["score_availability"]
      + w["priceedge"]*df["score_priceedge"]
      + w["logistics"]*df["score_logistics"]
      + w["risk"]*df["score_risk"]
      + w["stability"]*df["score_stability"]
    )
    return df

def add_detectors(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    numeric_cols = [
        "amazon_90d_oos",
        "score_demand",
        "margin_pct",
        "flipability_90d",
        "buybox_std_90d",
        "buybox_current",
        "buybox_pct_amz_90d",
        "total_offer_count",
        "return_rate",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df.get(col, pd.Series([0] * len(df), index=df.index)),
            errors="coerce",
        ).fillna(0)

    cond_window = (
        (df["amazon_90d_oos"] > 10)
        & (df["score_demand"] > 0.55)
        & (df["margin_pct"] > 0.12)
    )
    cond_flip = (
        (df["flipability_90d"] > 80)
        | (df["buybox_std_90d"] > (df["buybox_current"] * 0.12))
    ) & (df["score_demand"] > 0.45)
    cond_low_guard = (
        (df["buybox_pct_amz_90d"] < 0.2)
        & (df["total_offer_count"] <= 8)
    )
    cond_risk = (
        (df.get("map_restriction", "no").astype(str).str.lower().isin(["yes", "true", "1"]))
        | (df["return_rate"] > 0.15)
    )
    df["badge_window"] = cond_window.map({True: "Window Advantage", False: ""})
    df["badge_flip"] = cond_flip.map({True: "Volatility Flip", False: ""})
    df["badge_lowguard"] = cond_low_guard.map({True: "Low Guarded Buybox", False: ""})
    df["badge_risk"] = cond_risk.map({True: "Risk Alert", False: ""})
    df["badges"] = df[
        ["badge_window", "badge_flip", "badge_lowguard", "badge_risk"]
    ].apply(lambda r: ", ".join([b for b in r if b]), axis=1)
    return df
