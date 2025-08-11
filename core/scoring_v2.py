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
    cond_window = (
        (df.get("amazon_90d_oos", 0).fillna(0) > 10)
        & (df.get("score_demand", 0) > 0.55)
        & (df.get("margin_pct", 0) > 0.12)
    )
    cond_flip = (
        (df.get("flipability_90d", 0).fillna(0) > 80)
        | (df.get("buybox_std_90d", 0).fillna(0) > (df.get("buybox_current", 0).fillna(1)*0.12))
    ) & (df.get("score_demand", 0) > 0.45)
    cond_low_guard = (
        (df.get("buybox_pct_amz_90d", 0).fillna(0) < 0.2)
        & (df.get("total_offer_count", 0).fillna(0) <= 8)
    )
    cond_risk = (
        (df.get("map_restriction", "no").astype(str).str.lower().isin(["yes","true","1"]))
        | (df.get("return_rate", 0).fillna(0) > 0.15)
    )
    df["badge_window"] = cond_window.map({True:"Window Advantage", False:""})
    df["badge_flip"] = cond_flip.map({True:"Volatility Flip", False:""})
    df["badge_lowguard"] = cond_low_guard.map({True:"Low Guarded Buybox", False:""})
    df["badge_risk"] = cond_risk.map({True:"Risk Alert", False:""})
    df["badges"] = df[["badge_window","badge_flip","badge_lowguard","badge_risk"]].apply(
        lambda r: ", ".join([b for b in r if b]), axis=1
    )
    return df
