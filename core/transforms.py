from __future__ import annotations
import re
import pandas as pd

def to_country_from_locale(val: str) -> str:
    if not isinstance(val, str):
        return None
    v = val.strip().lower()
    if v in {"it", "it-it", "amazon.it"}: return "IT"
    if v in {"de", "de-de", "amazon.de"}: return "DE"
    if v in {"fr", "fr-fr", "amazon.fr"}: return "FR"
    if v in {"es", "es-es", "amazon.es"}: return "ES"
    if v in {"nl", "nl-nl", "amazon.nl"}: return "NL"
    if v in {"be", "be-be", "amazon.be"}: return "BE"
    if v in {"at", "de-at", "amazon.at"}: return "AT"
    if v in {"pl", "pl-pl", "amazon.pl"}: return "PL"
    if v in {"se", "sv-se", "amazon.se"}: return "SE"
    if v in {"dk", "da-dk", "amazon.dk"}: return "DK"
    if v in {"ie", "en-ie", "amazon.ie"}: return "IE"
    if v in {"pt", "pt-pt", "amazon.pt"}: return "PT"
    if v in {"gb", "uk", "en-gb", "amazon.co.uk"}: return "UK"
    m = re.search(r"([A-Za-z]{2})$", v)
    if m:
        code = m.group(1).upper()
        return "UK" if code == "GB" else code
    return v.upper()

def parse_price(x):
    if x is None: return None
    if isinstance(x, (int, float)): return float(x)
    s = str(x)
    if not s or s.strip().lower() in {"no", "nan", "none"}:
        return None
    s = re.sub(r"[€£$\s]", "", s)
    if "," in s and "." in s:
        s = s.replace(".", "")
        s = s.replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return None

def parse_percent(x):
    if x is None: return None
    if isinstance(x, (int, float)):
        val = float(x)
        return val/100.0 if val > 1 else val
    s = str(x).strip().lower().replace("%","")
    s = s.replace(",", ".")
    try:
        v = float(s)
        return v/100.0 if v > 1 else v
    except:
        return None

def parse_int(x):
    if x is None or x == "" or pd.isna(x):
        return None
    try:
        return int(float(x))
    except:
        return None

def coerce_numeric(df: pd.DataFrame, cols: list[str], fn) -> pd.DataFrame:
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = df[c].map(fn)
    return df

def ensure_country_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "country" not in df.columns:
        if "locale" in df.columns:
            df["country"] = df["locale"].map(to_country_from_locale)
        else:
            df["country"] = None
    return df
