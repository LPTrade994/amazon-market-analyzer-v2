from __future__ import annotations
import numpy as np
import pandas as pd

def _to_numeric(val):
    """Convert input to numeric, replacing non-convertible values with 0."""
    if np.isscalar(val):
        try:
            val = float(val)
        except (TypeError, ValueError):
            val = 0.0
        return 0.0 if np.isnan(val) else val
    val = pd.to_numeric(val, errors="coerce")
    if hasattr(val, "fillna"):
        return val.fillna(0)
    return np.nan_to_num(val, nan=0.0)

def _norm(x, low, high):
    x = _to_numeric(x)
    low = _to_numeric(low)
    high = _to_numeric(high)
    diff = high - low
    rng = np.nanmax(
        np.stack([diff, np.full_like(diff, 1e-9, dtype=float)], axis=0), axis=0
    )
    if np.isscalar(rng):
        rng = float(rng)
    v = (x - low) / rng
    return np.clip(v, 0.0, 1.0)

def safe_ratio(a, b):
    a = np.array(a, dtype=float); b = np.array(b, dtype=float)
    b[b==0] = np.nan
    r = a / b
    r = np.nan_to_num(r, nan=0.0, posinf=1.0, neginf=0.0)
    return r

def add_demand_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    sr = df.get("sales_rank_current")
    sr_term = _norm(-np.log1p(sr.fillna(sr.max() or 1)), -15, 0) if sr is not None else 0
    drops30 = _norm(df.get("sales_rank_drops_30d", 0).fillna(0), 0, 20)
    bought = _norm(df.get("bought_past_month", 0).fillna(0), 0, 2000)
    rev_growth = safe_ratio(df.get("reviews_count", 0).fillna(0), df.get("reviews_90d_avg", 1).replace(0,1))
    rev_term = _norm(rev_growth, 0.9, 1.5)
    df["score_demand"] = (sr_term + drops30 + bought + rev_term) / 4.0
    return df

def add_priceedge_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bb = df.get("buybox_current", pd.Series([np.nan]*len(df)))
    slp = df.get("suggested_lower_price", pd.Series([np.nan]*len(df)))
    thr = df.get("competitive_price_threshold", pd.Series([np.nan]*len(df)))
    std30 = _norm(df.get("buybox_std_30d", 0).fillna(0), 0, (df.get("buybox_current", 0).fillna(1)*0.25).max() if len(df)>0 else 1)
    flip90 = _norm(df.get("flipability_90d", 0).fillna(0), 0, 200)
    edge_thr = _norm((thr - bb).fillna(0), -50, 50)
    edge_slp = _norm((slp - bb).fillna(0), -50, 50)
    df["score_priceedge"] = (edge_thr + edge_slp + std30 + flip90) / 4.0
    return df

def add_competition_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    sellers = df.get("total_offer_count", pd.Series([np.nan]*len(df))).fillna(0)
    new_sellers = df.get("new_offer_count_current", pd.Series([np.nan]*len(df))).fillna(0)
    pct_amz_90 = df.get("buybox_pct_amz_90d", pd.Series([np.nan]*len(df))).fillna(0)
    winners90 = df.get("buybox_winner_cnt_90d", pd.Series([np.nan]*len(df))).fillna(0)
    s_term = 1 - _norm(sellers, 0, 50)
    ns_term = 1 - _norm(new_sellers, 0, 30)
    amz_term = 1 - _norm(pct_amz_90, 0.0, 1.0)
    win_term = 1 - _norm(winners90, 1, 25)
    df["score_competition"] = (s_term + ns_term + amz_term + win_term) / 4.0
    return df

def add_availability_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    oos90 = _norm(df.get("amazon_90d_oos", 0).fillna(0), 0, 90)
    oosc30 = _norm(df.get("amazon_oos_cnt_30d", 0).fillna(0), 0, 15)
    avail = df.get("amazon_offer_availability", "").astype(str).str.lower()
    no_amz = avail.str.contains("no amazon offer").astype(float)
    ship_delay = df.get("amazon_offer_shipping_delay", "").astype(str).str.contains("delay").astype(float)
    df["score_availability"] = (oos90 + oosc30 + no_amz + ship_delay) / 4.0
    return df

def add_stability_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    std90 = _norm(df.get("buybox_std_90d", 0).fillna(0), 0, (df.get("buybox_current", 0).fillna(1)*0.3).max() if len(df)>0 else 1)
    df["score_stability"] = (0.6 * (1 - std90)) + 0.4 * std90
    return df

def add_logistics_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    fee = df.get("fba_pickpack_fee", pd.Series([np.nan]*len(df))).fillna(0)
    weight = df.get("item_weight_g", pd.Series([np.nan]*len(df))).fillna(0)
    prime = df.get("prime_eligible", pd.Series(["no"]*len(df))).astype(str).str.lower().isin(["yes","true","1"]).astype(float)
    fee_term = 1 - _norm(fee, 0, 7.0)
    weight_term = 1 - _norm(weight, 0, 3000)
    df["score_logistics"] = (fee_term + weight_term + prime) / 3.0
    return df

def add_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    rr = df.get("return_rate", pd.Series([np.nan]*len(df))).fillna(0)
    rr_term = 1 - _norm(rr, 0, 0.2)
    map_flag = df.get("map_restriction", pd.Series(["no"]*len(df))).astype(str).str.lower().isin(["yes","true","1"]).astype(float)
    map_term = 1 - map_flag
    df["score_risk"] = (rr_term + map_term) / 2.0
    return df

def add_all_component_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = add_demand_score(df)
    df = add_priceedge_score(df)
    df = add_competition_score(df)
    df = add_availability_score(df)
    df = add_stability_score(df)
    df = add_logistics_score(df)
    df = add_risk_score(df)
    return df
