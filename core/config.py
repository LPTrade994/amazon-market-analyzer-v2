from __future__ import annotations

DEFAULT_VAT = {
    "IT": 0.22,
    "DE": 0.19,
    "ES": 0.21,
    "FR": 0.20,
    "UK": 0.20,
    "NL": 0.21,
    "BE": 0.21,
    "PL": 0.23,
    "SE": 0.25,
    "AT": 0.20,
}

# Valori di default per sconto gift card per paese (0..1). Modificabili da UI.
DEFAULT_DISCOUNT = {k: 0.0 for k in DEFAULT_VAT.keys()}

# Colonne suggerite per prezzi, fee, e segnali.
PRICE_COL_CANDIDATES = [
    "Buy Box 🚚: Current",
    "New: Current",
    "Amazon: Current",
]

SELL_SIGNALS = [
    "Sales Rank: Current",
    "Drops last 30 days",
    "Reviews: Rating",
    "Return Rate",
    "Buy Box: % Amazon 90 days",
]

FEE_COL_PICKPACK = "FBA Pick&Pack Fee"
FEE_COL_REF_PCT = "Referral Fee %"
FEE_COL_REF_CUR = "Referral Fee based on current Buy Box price"
TITLE_COL = "Title"
LOCALE_COL = "Locale"
ASIN_COL = "ASIN"