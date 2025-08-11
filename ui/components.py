from __future__ import annotations
import streamlit as st
import pandas as pd

def metric_card(col, label: str, value, delta=None):
    with col: st.metric(label, value, delta=delta)

def badges_cell(badges: str):
    tags = [t.strip() for t in (badges or "").split(",") if t.strip()]
    if not tags: return ""
    return " ".join([f"<span class='hdg-badge'>{t}</span>" for t in tags])

def render_leaderboard(df: pd.DataFrame, top_n: int = 200):
    if df.empty:
        st.info("Carica i dataset e seleziona i mercati per vedere i risultati.")
        return
    view_cols = [
        "opportunity_score_v2","gross_margin_eur","margin_pct",
        "score_demand","total_offer_count_sell","buybox_pct_amz_90d_sell",
        "amazon_90d_oos_sell","flipability_90d_sell",
        "country_buy","country_sell","asin","title_sell","pair_badges","url_amazon_sell","url_keepa_sell"
    ]
    present = [c for c in view_cols if c in df.columns]
    show = df.sort_values("opportunity_score_v2", ascending=False).head(top_n)[present].copy()
    if "margin_pct" in show.columns:
        show["margin_pct"] = (show["margin_pct"]*100).map(lambda v: f"{v:.1f}%")
    if "gross_margin_eur" in show.columns:
        show["gross_margin_eur"] = show["gross_margin_eur"].map(lambda v: f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
    if "opportunity_score_v2" in show.columns:
        show["opportunity_score_v2"] = show["opportunity_score_v2"].map(lambda v: f"{v:.3f}")
    if "pair_badges" in show.columns:
        show["pair_badges"] = show["pair_badges"].apply(lambda s: badges_cell(s))
    st.write(show.to_html(escape=False, index=False), unsafe_allow_html=True)
