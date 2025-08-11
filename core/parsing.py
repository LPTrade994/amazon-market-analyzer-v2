from __future__ import annotations
import math
import re
import pandas as pd
import numpy as np
from typing import Optional

NON_DIGIT_DEC = re.compile(r"[^0-9,.-]")

ISO2_FIX = {
    "gb": "UK",
    "uk": "UK",
}

# Normalizza stringhe come "it", "it-IT", "Amazon.de", "de-DE" in ISO2 (IT, DE, ES, ...)
def normalize_locale(s: str | float | None) -> Optional[str]:
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return None
    t = str(s).strip().lower()
    if not t:
        return None
    code: Optional[str] = None

    # Amazon.tld
    if "amazon." in t:
        tld = t.split("amazon.")[-1]
        tld = tld.split("/")[0].split()[0]
        tld = tld.replace("co.uk", "uk")
        code = tld[:2]
    # xx-YY
    if code is None:
        m = re.search(r"\b([a-z]{2})-[a-z]{2}\b", t)
        if m:
            code = m.group(1)
    # plain xx
    if code is None:
        m2 = re.search(r"\b([a-z]{2})\b", t)
        if m2:
            code = m2.group(1)

    if code is None:
        return None
    code = ISO2_FIX.get(code, code).upper()
    return code

# Parse prezzo tipo "399,00 €", "1.234,56", "1 234,56", "399€", "399" → float

def parse_price(val) -> float | np.nan:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return np.nan
    s = str(val).strip()
    if not s:
        return np.nan
    s = s.replace("\xa0", " ")
    s = s.replace("EUR", "").replace("€", "").strip()
    s = NON_DIGIT_DEC.sub("", s)
    if not s:
        return np.nan

    # Decide decimal separator based on last occurrence
    last_comma = s.rfind(",")
    last_dot = s.rfind(".")

    if last_comma == -1 and last_dot == -1:
        return float(s)

    if last_comma > last_dot:
        # comma is decimal sep → remove dots (thousands), replace comma with dot
        s = s.replace(".", "")
        s = s.replace(",", ".")
    else:
        # dot is decimal → remove commas (thousands)
        s = s.replace(",", "")

    try:
        return float(s)
    except ValueError:
        return np.nan

# Parse percentuali "7,00 %" → 0.07

def parse_pct(val) -> float | np.nan:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return np.nan
    s = str(val).strip().replace("%", "").strip()
    x = parse_price(s)
    if np.isnan(x):
        return np.nan
    return x / 100.0

# Utility: trova la prima colonna esistente tra candidate

def first_present(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None