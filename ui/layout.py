from __future__ import annotations
import streamlit as st
import pandas as pd
from .components import metric_card, render_leaderboard

def sidebar_controls(countries: list[str]):
    st.sidebar.header("Dataset & Parametri")
    buy_sel = st.sidebar.multiselect("Paesi ACQUISTO", options=countries, default=[c for c in countries if c!="IT"] or countries)
    sell_sel = st.sidebar.multiselect("Paesi VENDITA", options=countries, default=["IT"] if "IT" in countries else countries[:1])
    ship_mode = st.sidebar.radio("Modalità spedizione per VENDITA", ["FBA","FBM"], index=0, horizontal=True)

    st.sidebar.write("---")
    st.sidebar.subheader("Pesi punteggio (v2)")
    w_margin = st.sidebar.slider("Margine", 0.0, 1.0, 0.35, 0.01)
    w_demand = st.sidebar.slider("Domanda", 0.0, 1.0, 0.20, 0.01)
    w_comp = st.sidebar.slider("Concorrenza", 0.0, 1.0, 0.12, 0.01)
    w_avail = st.sidebar.slider("Disponibilità", 0.0, 1.0, 0.10, 0.01)
    w_price = st.sidebar.slider("Vantaggio Prezzo", 0.0, 1.0, 0.10, 0.01)
    w_log = st.sidebar.slider("Logistica", 0.0, 1.0, 0.06, 0.01)
    w_risk = st.sidebar.slider("Rischio", 0.0, 1.0, 0.04, 0.01)
    w_stab = st.sidebar.slider("Stabilità", 0.0, 1.0, 0.03, 0.01)

    st.sidebar.write("---")
    st.sidebar.subheader("Sconti per Paese (Acquisto)")
    discount_map = {}
    for c in sorted(set(buy_sel)):
        discount_map[c] = st.sidebar.number_input(f"Sconto {c}", 0.0, 0.9, 0.0, 0.01, key=f"disc_{c}")
    return buy_sel, sell_sel, ship_mode, {
        "margin": w_margin, "demand": w_demand, "competition": w_comp, "availability": w_avail,
        "priceedge": w_price, "logistics": w_log, "risk": w_risk, "stability": w_stab
    }, discount_map

def top_kpis(col1, col2, col3, df_pairs):
    if df_pairs is None or df_pairs.empty:
        metric_card(col1, "#ASIN", 0)
        metric_card(col2, "#Coppie mercato", 0)
        metric_card(col3, "Margine medio", "—")
        return
    metric_card(col1, "#ASIN", df_pairs["asin"].nunique())
    metric_card(col2, "#Coppie mercato", len(df_pairs))
    try:
        metric_card(col3, "Margine medio", f"€ {df_pairs['gross_margin_eur'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
    except Exception:
        metric_card(col3, "Margine medio", "—")

def discover_tab(df_ranked: pd.DataFrame):
    st.subheader("Classifica Opportunità (Score v2)")
    render_leaderboard(df_ranked)
