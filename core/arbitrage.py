from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Callable
from .config import DEFAULT_VAT, REFERRAL_FEE_DEFAULT, FBM_FLAT_EUR, PRICE_COL_BUY_CANDIDATES, PRICE_COL_SELL

def pick_buy_price(row: pd.Series) -> float | None:
    for c in PRICE_COL_BUY_CANDIDATES:
        col = f"{c}_buy" if f"{c}_buy" in row.index else c
        v = row.get(col, None)
        if pd.notna(v):
            return float(v)
    return None

def estimate_fees(sell_price: float, referral_pct: float | None, fba_pickpack: float | None, ship_mode: str) -> float:
    ref = (referral_pct if referral_pct is not None else REFERRAL_FEE_DEFAULT)
    referral_fee = sell_price * ref
    if ship_mode.upper() == "FBA":
        return referral_fee + float(fba_pickpack or 0.0)
    return referral_fee + FBM_FLAT_EUR

def build_pairs(df: pd.DataFrame, buy_countries: list[str], sell_countries: list[str]) -> pd.DataFrame:
    buy_df = df[df["country"].isin(buy_countries)].copy()
    sell_df = df[df["country"].isin(sell_countries)].copy()
    pairs = buy_df.merge(sell_df, on="asin", how="inner", suffixes=("_buy","_sell"))
    return pairs

def compute_margins(
    pairs: pd.DataFrame,
    vat_sell_map: Dict[str, float] | None,
    discount_map: Dict[str, float] | None,
    ship_mode: str,
    vat_discount_fn: Callable[[float, float, float, str], float],
) -> pd.DataFrame:
    res = pairs.copy()

    # buy price
    res["buy_price"] = res.apply(lambda r: pick_buy_price(r), axis=1)

    # sell price
    sell_col = "buybox_current_sell"
    if sell_col not in res.columns:
        raise ValueError("Colonna prezzo vendita non trovata (buybox_current_sell). Verifica il dataset SELL.")
    res["sell_price"] = res[sell_col].astype(float)

    # VATs
    vat_map = DEFAULT_VAT.copy()
    if vat_sell_map:
        vat_map.update({k.upper(): v for k, v in vat_sell_map.items()})

    res["vat_buy"] = res["country_buy"].map(lambda c: vat_map.get(str(c).upper(), 0.22))
    res["vat_sell"] = res["country_sell"].map(lambda c: vat_map.get(str(c).upper(), 0.22))
    res["discount_buy"] = res["country_buy"].map(lambda c: (discount_map or {}).get(str(c).upper(), 0.0))

    # Net buy using EXISTING rules (kept unchanged)
    res["buy_net"] = res.apply(
        lambda r: float(vat_discount_fn(r["buy_price"], r["vat_buy"], r["discount_buy"], str(r["country_buy"])))
        if pd.notna(r["buy_price"]) else np.nan, axis=1
    )

    # Net sell
    res["sell_net"] = res["sell_price"] / (1.0 + res["vat_sell"].fillna(0.0))

    # Fees
    referral_pct = res.get("referral_fee_pct_sell", res.get("referral_fee_pct", np.nan)).fillna(np.nan)
    fba_pickpack = res.get("fba_pickpack_fee_sell", res.get("fba_pickpack_fee", 0)).fillna(0)
    referral_pct = referral_pct.map(lambda v: (v/100.0) if (pd.notna(v) and v>1) else v)

    res["fees"] = [
        estimate_fees(float(sp or 0), float(rp) if pd.notna(rp) else None, float(pp or 0), ship_mode)
        for sp, rp, pp in zip(res["sell_price"], referral_pct, fba_pickpack)
    ]

    # Margins
    res["gross_margin_eur"] = res["sell_net"] - res["fees"] - res["buy_net"]
    res["margin_pct"] = res["gross_margin_eur"] / res["buy_net"].replace({0: np.nan})

    return res

def attach_badges_for_pairs(df_pairs: pd.DataFrame) -> pd.DataFrame:
    df = df_pairs.copy()
    cond_no_amz = df.get("amazon_offer_availability_sell","").astype(str).str.contains("no amazon offer", case=False, na=False)
    cond_oos90 = pd.to_numeric(df.get("amazon_90d_oos_sell", 0), errors="coerce").fillna(0) > 10
    cond_low_amz_pct = pd.to_numeric(df.get("buybox_pct_amz_90d_sell", 0), errors="coerce").fillna(0) < 0.2
    cond_few_sellers = pd.to_numeric(df.get("total_offer_count_sell", 0), errors="coerce").fillna(0) <= 8
    df["pair_badges"] = (
        cond_no_amz.map({True:"No Amazon", False:""}).fillna("")
        + cond_oos90.map({True:" OOS90", False:""}).fillna("")
        + cond_low_amz_pct.map({True:" Low%AMZ", False:""}).fillna("")
        + cond_few_sellers.map({True:" FewSellers", False:""}).fillna("")
    ).str.strip()
    return df
