from __future__ import annotations
import streamlit as st
import pandas as pd
import os

from core.loaders import load_many
from core.config import DEFAULT_VAT
from core.arbitrage import build_pairs, compute_margins, attach_badges_for_pairs
from core.scoring_v2 import add_opportunity_score, add_detectors
from ui.layout import sidebar_controls, top_kpis, discover_tab
from utils import apply_vat_discount_rules

st.set_page_config(page_title="Amazon Market Analyzer – v2", layout="wide", page_icon="🕵️")

# load CSS
try:
    with open(os.path.join("ui","style.css"), "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.title("Amazon Market Analyzer – Score v2")
st.caption("IVA & Sconto: **INVARIATI** – motore opportunità migliorato.")

# Upload
files = st.file_uploader("Carica uno o più dataset Keepa (CSV/XLSX) – multi-paese", type=["csv","xlsx"], accept_multiple_files=True)
if not files:
    st.info("Suggerimento: puoi caricare IT/DE/FR/ES insieme; verranno unificati automaticamente.")
    st.stop()

df_all = load_many(files)
if df_all.empty:
    st.error("Nessun dato caricato.")
    st.stop()

# Countries
countries = sorted([c for c in df_all["country"].dropna().unique().tolist() if c])

# Sidebar
buy_sel, sell_sel, ship_mode, weights, discount_map = sidebar_controls(countries)

# Pairs & margins
pairs = build_pairs(df_all, buy_sel, sell_sel)
if pairs.empty:
    st.warning("Nessuna coppia mercato generata: verifica che gli ASIN coincidano tra i paesi selezionati.")
    st.stop()

with st.spinner("Calcolo margini e punteggi..."):
    df_marg = compute_margins(
        pairs=pairs,
        vat_sell_map=DEFAULT_VAT,
        discount_map=discount_map or {},
        ship_mode=ship_mode,
        vat_discount_fn=apply_vat_discount_rules,
    )

    # Usa SELL-side per domanda/concorrenza ecc.
    sell_cols = {c: c.replace("_sell","") for c in df_marg.columns if c.endswith("_sell")}
    df_sell = df_marg.rename(columns=sell_cols).copy()

    df_scored = add_opportunity_score(df_sell, weights=weights)
    df_scored = add_detectors(df_scored)
    df_scored = attach_badges_for_pairs(df_scored)

# KPIs
c1, c2, c3 = st.columns(3)
top_kpis(c1, c2, c3, df_scored)

# Leaderboard
discover_tab(df_scored)

# Download
st.download_button(
    "Scarica risultati (CSV)",
    data=df_scored.to_csv(index=False).encode("utf-8"),
    file_name="ama_v2_results.csv",
    mime="text/csv"
)
