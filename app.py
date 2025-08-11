from __future__ import annotations
import io
import pandas as pd
import numpy as np
import streamlit as st

from core.config import (
    DEFAULT_VAT, DEFAULT_DISCOUNT, PRICE_COL_CANDIDATES,
    SELL_SIGNALS, FEE_COL_PICKPACK, FEE_COL_REF_PCT, FEE_COL_REF_CUR,
    TITLE_COL, LOCALE_COL, ASIN_COL,
)
from core.parsing import normalize_locale, parse_price, parse_pct, first_present
from core.pricing import net_cost_purchase, net_proceeds_sale
from core.metrics import compute_score

st.set_page_config(page_title="Amazon Arbitrage Manager", layout="wide")
st.title("Amazon Arbitrage Manager")
st.caption("Upload dataset Keepa (anche multi-paese), applica regole IVA + sconto, calcola margine/ROI e trova le migliori opportunità.")

# --- Sidebar: Config ---------------------------------------------------------
st.sidebar.header("Impostazioni")

# VAT & Discount maps (persist)
if "vat_map" not in st.session_state:
    st.session_state.vat_map = DEFAULT_VAT.copy()
if "discount_map" not in st.session_state:
    st.session_state.discount_map = DEFAULT_DISCOUNT.copy()

# Upload multipli per ORIGINE (multi-paese)
origin_files = st.sidebar.file_uploader(
    "File di ACQUISTO (origine) – XLSX (puoi caricarne più di uno)",
    type=["xlsx", "xls"], accept_multiple_files=True, key="orig_multi")

# Opzionale: un file di VENDITA (target)
file_sell = st.sidebar.file_uploader(
    "File di VENDITA (target, opzionale) – XLSX", type=["xlsx", "xls"], key="sell")

sell_mode = st.sidebar.selectbox("Modalità vendita", ["FBA", "FBM"], index=0)
shipping_fbm = 0.0
if sell_mode == "FBM":
    shipping_fbm = st.sidebar.number_input("Costo spedizione FBM per unità (€)", min_value=0.0, value=0.0, step=0.1)

apply_coupons = st.sidebar.toggle("Considera Coupon/Business Discount sul prezzo di vendita (stima)", value=False)

exclude_refurb = st.sidebar.toggle("Escludi Ricondizionato/Renewed", value=True)

# --- Helpers -----------------------------------------------------------------

def load_xlsx(f) -> pd.DataFrame:
    return pd.read_excel(f, engine="openpyxl")

@st.cache_data(show_spinner=False)
def process_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if LOCALE_COL in df.columns:
        df["CountryCode"] = df[LOCALE_COL].apply(normalize_locale)
    else:
        df["CountryCode"] = None
    return df

# Choose price column from candidates

def choose_price_column(df: pd.DataFrame, label: str):
    default_col = first_present(df, PRICE_COL_CANDIDATES) or df.columns[0]
    return st.selectbox(label, options=df.columns, index=list(df.columns).index(default_col) if default_col in df.columns else 0)

# --- Load ORIGINE (multi-file concat) ---------------------------------------

if not origin_files:
    st.info("Carica almeno **un file di acquisto (origine)** dalla sidebar per iniziare. Puoi caricarne più di uno (multi-paese).")
    st.stop()

orig_frames = []
for f in origin_files:
    tmp = load_xlsx(f)
    tmp = process_df(tmp)
    tmp["SourceFile"] = f.name
    orig_frames.append(tmp)
orig_df_raw = pd.concat(orig_frames, ignore_index=True, sort=False)
orig_df = orig_df_raw.copy()

# VENDITA
if file_sell:
    sell_df_raw = load_xlsx(file_sell)
    sell_df = process_df(sell_df_raw)
else:
    sell_df_raw = None
    sell_df = None

# Countries (per editor IVA/sconto)
countries = sorted(list(set([c for c in orig_df.get("CountryCode", []) if pd.notna(c)])))
if sell_df is not None:
    sell_countries = sorted(list(set([c for c in sell_df.get("CountryCode", []) if pd.notna(c)])))
    for c in sell_countries:
        if c not in countries:
            countries.append(c)

# Editor IVA
vat_rows = [{"Country": c, "VAT": st.session_state.vat_map.get(c, DEFAULT_VAT.get(c, 0.22))} for c in (countries or list(DEFAULT_VAT.keys()))]
vat_df = pd.DataFrame(vat_rows)
vat_df = st.sidebar.data_editor(vat_df, use_container_width=True, num_rows="dynamic", key="vat_editor")
st.session_state.vat_map.update({row["Country"]: float(row["VAT"]) for _, row in vat_df.iterrows() if row.get("Country")})

# Editor sconti
disc_rows = [{"Country": c, "Discount": st.session_state.discount_map.get(c, 0.0)} for c in (countries or list(DEFAULT_VAT.keys()))]
disc_df = pd.DataFrame(disc_rows)
disc_df = st.sidebar.data_editor(disc_df, use_container_width=True, num_rows="dynamic", key="disc_editor")
st.session_state.discount_map.update({row["Country"]: float(row["Discount"]) for _, row in disc_df.iterrows() if row.get("Country")})

# Marketplace di vendita se non c'è file target
sell_market_if_single = st.sidebar.selectbox(
    "Marketplace di vendita (se non carichi file target)",
    options=list(st.session_state.vat_map.keys()),
    index=list(st.session_state.vat_map.keys()).index("IT") if "IT" in st.session_state.vat_map else 0
)

# Colonne prezzo
purchase_price_col = choose_price_column(orig_df, "Colonna PREZZO di ACQUISTO (origine)")
if sell_df is not None:
    sell_price_col = choose_price_column(sell_df, "Colonna PREZZO di VENDITA (target)")
else:
    sell_price_col = choose_price_column(orig_df, "Colonna PREZZO di VENDITA (se assente file target, dal file origine)")

# Fees fallback
referral_pct_fallback = st.sidebar.number_input("Referral Fee % (fallback)", min_value=0.0, max_value=1.0, value=0.15, step=0.01,
                                               help="Usato se non presente nel dataset come percentuale o fee fissa.")
fba_fee_fallback = st.sidebar.number_input("FBA Pick&Pack Fee (€) (fallback)", min_value=0.0, value=0.0, step=0.1)
other_costs_sell = st.sidebar.number_input("Altri costi di vendita per unità (€)", min_value=0.0, value=0.0, step=0.1)

# --- Prepare views -----------------------------------------------------------

def prepare_side(df: pd.DataFrame, price_col: str, role: str):
    view_cols = [c for c in [ASIN_COL, TITLE_COL, LOCALE_COL, "CountryCode", "SourceFile", price_col,
                             "Return Rate", "Reviews: Rating", "Sales Rank: Current",
                             "Drops last 30 days", "Buy Box: % Amazon 90 days",
                             "Amazon: 90 days OOS", "Amazon: OOS Count 90 days",
                             "Buy Box: Standard Deviation 90 days",
                             FEE_COL_PICKPACK, FEE_COL_REF_PCT, FEE_COL_REF_CUR,
                             "Bought in past month", "One Time Coupon: Absolute",
                             "One Time Coupon: Percentage", "Business Discount: Percentage"] if c in df.columns]
    x = df[view_cols].copy()
    x.rename(columns={price_col: f"{role}Price_Gross"}, inplace=True)
    x[f"{role}Price_Gross"] = x[f"{role}Price_Gross"].apply(parse_price)
    if "CountryCode" not in x.columns:
        x["CountryCode"] = df.get("CountryCode")
    return x

orig_side = prepare_side(orig_df, purchase_price_col, role="Purchase")

if sell_df is not None:
    sell_side = prepare_side(sell_df, sell_price_col, role="Sell")
else:
    sell_side = prepare_side(orig_df, sell_price_col, role="Sell")
    sell_side["CountryCode"] = sell_market_if_single
    sell_side["SourceFile"] = sell_side.get("SourceFile", pd.Series(["origin"]*len(sell_side)))

# Merge per ASIN (mantiene più righe origine per ASIN)
base = pd.merge(
    orig_side, sell_side.drop(columns=[TITLE_COL, LOCALE_COL], errors='ignore'),
    on=ASIN_COL, suffixes=("_o", "_s"), how="left"
)

# Title prefer origin
if TITLE_COL in orig_side.columns and TITLE_COL not in base.columns:
    base[TITLE_COL] = orig_side[TITLE_COL]

# Filtro ricondizionato
if exclude_refurb and TITLE_COL in base.columns:
    mask = ~base[TITLE_COL].str.contains("ricondizionato|renewed", case=False, na=False)
    base = base[mask]

# VAT map
vat_map = st.session_state.vat_map
base["VAT_Origine"] = base["CountryCode_o"].apply(lambda c: float(vat_map.get(c, vat_map.get("IT", 0.22))))
base["VAT_Vendita"] = base["CountryCode_s"].apply(lambda c: float(vat_map.get(c, vat_map.get("IT", 0.22))))

# Discount override merge (se esiste)
if "Discount_Override" in orig_df.columns:
    base = base.merge(orig_df[[ASIN_COL, "Discount_Override"]], on=ASIN_COL, how="left")
else:
    base["Discount_Override"] = np.nan

# Discount applicato (origine)
base["Discount_Applied_Origine"] = base.apply(
    lambda r: float(st.session_state.discount_map.get(str(r.get("CountryCode_o")) if pd.notna(r.get("CountryCode_o")) else "IT", 0.0))
              if pd.isna(r["Discount_Override"]) else float(r["Discount_Override"]),
    axis=1
).clip(0.0, 1.0)

# NetCost d'acquisto
base["NetCost_Purchase"] = base.apply(lambda r: net_cost_purchase(
    price_gross=r.get("PurchasePrice_Gross"),
    country_code=r.get("CountryCode_o"),
    discount=r.get("Discount_Applied_Origine"),
    vat_map=vat_map
), axis=1)

# Prezzo vendita lordo (eventuale applicazione coupon/BD)
base["SellPrice_Gross"] = base["SellPrice_Gross"].astype(float)

if apply_coupons:
    # unisci dati coupon dal frame sorgente appropriato
    ref_df = sell_df_raw if sell_df_raw is not None else orig_df_raw
    join_cols = {"One Time Coupon: Absolute": "_abs_coupon",
                 "One Time Coupon: Percentage": "_pct_coupon",
                 "Business Discount: Percentage": "_bd_pct"}
    for src_col, alias in join_cols.items():
        if src_col in ref_df.columns:
            tmp = pd.DataFrame({ASIN_COL: ref_df[ASIN_COL], alias: ref_df[src_col]})
            if "Percentage" in src_col:
                tmp[alias] = tmp[alias].apply(parse_pct)
            else:
                tmp[alias] = tmp[alias].apply(parse_price)
            base = base.merge(tmp, on=ASIN_COL, how="left")
    if "_abs_coupon" in base.columns:
        base["SellPrice_Gross"] = (base["SellPrice_Gross"] - base["_abs_coupon"].fillna(0.0)).clip(lower=0.0)
    if "_pct_coupon" in base.columns:
        base["SellPrice_Gross"] = base["SellPrice_Gross"] * (1.0 - base["_pct_coupon"].fillna(0.0))
    if "_bd_pct" in base.columns:
        base["SellPrice_Gross"] = base["SellPrice_Gross"] * (1.0 - base["_bd_pct"].fillna(0.0))

# Fees maps
ref_source = sell_df_raw if sell_df_raw is not None else orig_df_raw
if FEE_COL_REF_CUR in ref_source.columns:
    base = base.merge(pd.DataFrame({ASIN_COL: ref_source[ASIN_COL], "_ref_fixed": ref_source[FEE_COL_REF_CUR].apply(parse_price)}), on=ASIN_COL, how="left")
if FEE_COL_REF_PCT in ref_source.columns:
    base = base.merge(pd.DataFrame({ASIN_COL: ref_source[ASIN_COL], "_ref_pct": ref_source[FEE_COL_REF_PCT].apply(parse_pct)}), on=ASIN_COL, how="left")

# FBA fee
if sell_mode == "FBA":
    if FEE_COL_PICKPACK in ref_source.columns:
        base = base.merge(pd.DataFrame({ASIN_COL: ref_source[ASIN_COL], "_fba_fee": ref_source[FEE_COL_PICKPACK].apply(parse_price)}), on=ASIN_COL, how="left")
    else:
        base["_fba_fee"] = fba_fee_fallback
else:
    base["_fba_fee"] = 0.0

# Referral fallback
base["_ref_pct"] = base.get("_ref_pct", pd.Series([np.nan]*len(base))).fillna(referral_pct_fallback)

# Ricavi netti vendita
base["NetProceeds_Sale"] = base.apply(lambda r: net_proceeds_sale(
    sell_price_gross=r.get("SellPrice_Gross"),
    vat_sell=r.get("VAT_Vendita", 0.22),
    referral_fee_pct=r.get("_ref_pct"),
    referral_fee_fixed=r.get("_ref_fixed"),
    fba_fee=r.get("_fba_fee"),
    shipping_fbm=shipping_fbm,
    other_costs_sell=other_costs_sell,
), axis=1)

# Profit
base["Unit_Margin€"] = base["NetProceeds_Sale"] - base["NetCost_Purchase"]
base["ROI"] = base["Unit_Margin€"] / base["NetCost_Purchase"]

# --- PRESET FILTRI -----------------------------------------------------------

st.subheader("Filtri & Preset")
with st.expander("Preset rapidi", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        use_fast = st.checkbox("Veloci & Stabili", value=False)
        min_drops = st.number_input("Min Drops 30g", 0, 10_000, 10)
        min_bought = st.number_input("Min Bought past month", 0, 10_000, 200)
        max_std_pct = st.number_input("Max BB StdDev 90g / prezzo", 0.0, 1.0, 0.025, step=0.005)
    with c2:
        use_oos = st.checkbox("OOS Amazon", value=False)
        amazon_pct_max = st.number_input("Max BuyBox % Amazon 90g", 0.0, 1.0, 0.1, step=0.05)
        oos_days_min = st.number_input("Min OOS Count 90g (Amazon)", 0, 1000, 10)
    with c3:
        use_coupon = st.checkbox("Promo/Coupon", value=False)
        min_coupon_pct = st.number_input("Min Coupon/BD %", 0.0, 1.0, 0.05, step=0.01)
        max_std30 = st.number_input("Max BB StdDev 30g (€/abs)", 0.0, 1000.0, 10.0, step=0.5)

# build mask
mask_all = pd.Series([True]*len(base))

# Utility getters
bb_std90 = pd.to_numeric(base.get("Buy Box: Standard Deviation 90 days"), errors='coerce')
sell_gross = pd.to_numeric(base.get("SellPrice_Gross"), errors='coerce')
std_pct = bb_std90 / sell_gross.replace(0, np.nan)

if use_fast:
    cond_demand = (pd.to_numeric(base.get("Drops last 30 days"), errors='coerce') >= min_drops) | \
                  (pd.to_numeric(base.get("Bought in past month"), errors='coerce') >= min_bought)
    cond_stable = (std_pct <= max_std_pct)
    amz_col = "Buy Box: % Amazon 90 days"
    amz_series = base[amz_col] if amz_col in base.columns else pd.Series([np.nan]*len(base))
    if amz_series.dtype == object:
        amz_series = amz_series.apply(parse_pct)
    amazon_pct = pd.to_numeric(amz_series, errors='coerce')
    cond_amz = (amazon_pct.fillna(0) <= amazon_pct_max)
    mask_all &= cond_demand.fillna(False) & cond_stable.fillna(False) & cond_amz.fillna(False)

if use_oos:
    amz_col = "Buy Box: % Amazon 90 days"
    amz_series = base[amz_col] if amz_col in base.columns else pd.Series([np.nan]*len(base))
    if amz_series.dtype == object:
        amz_series = amz_series.apply(parse_pct)
    amazon_pct = pd.to_numeric(amz_series, errors='coerce')
    if pd.notna(amazon_pct.max()) and amazon_pct.max() > 1.0:
        # se è in % (0..100), normalizza
        amazon_pct = amazon_pct/100.0
    cond_amz_low = (amazon_pct.fillna(0) <= amazon_pct_max)
    oos_count = pd.to_numeric(base.get("Amazon: OOS Count 90 days"), errors='coerce')
    cond_oos = (oos_count.fillna(0) >= oos_days_min)
    mask_all &= cond_amz_low & cond_oos

if use_coupon:
    coupon_pct = pd.to_numeric(base.get("One Time Coupon: Percentage").apply(parse_pct) if "One Time Coupon: Percentage" in base.columns else pd.Series([np.nan]*len(base)), errors='coerce')
    bd_pct = pd.to_numeric(base.get("Business Discount: Percentage").apply(parse_pct) if "Business Discount: Percentage" in base.columns else pd.Series([np.nan]*len(base)), errors='coerce')
    cond_coupon = (coupon_pct.fillna(0) >= min_coupon_pct) | (bd_pct.fillna(0) >= min_coupon_pct) | (pd.to_numeric(base.get("One Time Coupon: Absolute"), errors='coerce').fillna(0) > 0)
    std30 = pd.to_numeric(base.get("Buy Box: Standard Deviation 30 days"), errors='coerce') if "Buy Box: Standard Deviation 30 days" in base.columns else pd.Series([0]*len(base))
    cond_stable30 = (std30.fillna(0) <= max_std30)
    mask_all &= cond_coupon & cond_stable30

filtered = base[mask_all].copy()

st.write(f"**Righe totali:** {len(base)} · **Dopo filtri:** {len(filtered)}")

# --- Score & Results tables --------------------------------------------------

filtered["Score"] = compute_score(filtered)

show_cols = [
    ASIN_COL, TITLE_COL,
    "CountryCode_o", "SourceFile_o", "VAT_Origine", "Discount_Applied_Origine", "PurchasePrice_Gross", "NetCost_Purchase",
    "CountryCode_s", "VAT_Vendita", "SellPrice_Gross", "_ref_pct", "_ref_fixed", "_fba_fee", "NetProceeds_Sale",
    "Unit_Margin€", "ROI", "Score",
    "Drops last 30 days", "Sales Rank: Current", "Buy Box: % Amazon 90 days", "Amazon: OOS Count 90 days"
]
show_cols = [c for c in show_cols if c in filtered.columns]

disp = filtered[show_cols].copy()
disp["ROI"] = (disp["ROI"]*100).map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
for c in ["PurchasePrice_Gross", "NetCost_Purchase", "SellPrice_Gross", "_ref_fixed", "_fba_fee", "NetProceeds_Sale", "Unit_Margin€"]:
    if c in disp.columns:
        disp[c] = pd.to_numeric(filtered[c], errors='coerce').map(lambda x: f"€ {x:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".") if pd.notna(x) else "")
for c in ["VAT_Origine", "VAT_Vendita", "_ref_pct", "Discount_Applied_Origine"]:
    if c in disp.columns:
        disp[c] = pd.to_numeric(filtered[c], errors='coerce').map(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "")

st.subheader("Risultati (post-filtri)")
st.dataframe(disp, use_container_width=True, height=500)

# --- MIGLIOR SOURCING PER ASIN (multi-paese) --------------------------------

st.subheader("Miglior sourcing per ASIN (multi-paese)")
if len(filtered):
    # scegli riga con NetCost_Purchase minimo per ASIN
    idx = filtered.groupby(ASIN_COL)["NetCost_Purchase"].idxmin()
    best = filtered.loc[idx].copy()
    best = best.sort_values("ROI", ascending=False)

    cols_best = [ASIN_COL, TITLE_COL, "CountryCode_o", "SourceFile_o", "NetCost_Purchase", "SellPrice_Gross", "Unit_Margin€", "ROI", "Score"]
    cols_best = [c for c in cols_best if c in best.columns]
    out = best[cols_best].copy()
    out["ROI"] = (out["ROI"]*100).map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
    for c in ["NetCost_Purchase", "SellPrice_Gross", "Unit_Margin€"]:
        if c in out.columns:
            out[c] = pd.to_numeric(best[c], errors='coerce').map(lambda x: f"€ {x:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".") if pd.notna(x) else "")

    st.dataframe(out.head(50), use_container_width=True)

    # download best
    def to_csv_bytes(df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")
    def to_xlsx_bytes(df: pd.DataFrame) -> bytes:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="best_sources")
        buf.seek(0)
        return buf.read()

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Scarica BEST CSV", data=to_csv_bytes(best), file_name="best_sources.csv", mime="text/csv")
    with c2:
        st.download_button("Scarica BEST XLSX", data=to_xlsx_bytes(best), file_name="best_sources.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Esporta risultati completi ---------------------------------------------

st.markdown("### Esporta risultati completi")

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="results")
    out.seek(0)
    return out.read()

c1, c2 = st.columns(2)
with c1:
    st.download_button("Scarica CSV (post-filtri)", data=to_csv_bytes(filtered), file_name="arbitrage_results_filtered.csv", mime="text/csv")
with c2:
    st.download_button("Scarica XLSX (post-filtri)", data=to_xlsx_bytes(filtered), file_name="arbitrage_results_filtered.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.caption("Tip: usa i preset per restringere a prodotti stabili/veloci, sfrutta la vista *Miglior sourcing* per scegliere il paese più conveniente.")
