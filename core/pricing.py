from __future__ import annotations
import math
import numpy as np
from typing import Optional, Dict

# Default IVA map; può essere sovrascritta da UI
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

# Sconto predefinito per paese (0..1). Sovrascrivibile da UI o per-riga via Discount_Override
DEFAULT_DISCOUNT = {k: 0.0 for k in DEFAULT_VAT.keys()}


def clamp_discount(d: Optional[float]) -> float:
    try:
        d = float(d)
    except (TypeError, ValueError):
        d = 0.0
    return max(0.0, min(1.0, d))


def vat_for(country_code: Optional[str], vat_map: Dict[str, float]) -> float:
    if not country_code:
        return vat_map.get("IT", 0.22)
    return vat_map.get(country_code, vat_map.get("IT", 0.22))


def net_cost_purchase(price_gross: Optional[float], country_code: Optional[str],
                      discount: Optional[float], vat_map: Dict[str, float]) -> float | np.nan:
    """
    Calcolo del costo netto d'acquisto secondo le tue regole:
      - Estero (≠ IT): Net = Price / (1 + VAT) * (1 - Discount)
      - Italia (IT):  Net = Price / (1 + VAT) - Price * Discount
    Dove Price è il prezzo lordo del marketplace, VAT l'aliquota del paese (0..1), Discount (0..1).
    """
    if price_gross is None or (isinstance(price_gross, float) and math.isnan(price_gross)):
        return np.nan
    vat = vat_for(country_code, vat_map)
    d = clamp_discount(discount)
    if (country_code or "").upper() == "IT":
        return price_gross / (1.0 + vat) - price_gross * d
    else:
        return (price_gross / (1.0 + vat)) * (1.0 - d)


def net_proceeds_sale(sell_price_gross: Optional[float], vat_sell: float,
                      referral_fee_pct: Optional[float] = None,
                      referral_fee_fixed: Optional[float] = None,
                      fba_fee: Optional[float] = None,
                      shipping_fbm: float = 0.0,
                      other_costs_sell: float = 0.0) -> float | np.nan:
    """Ricavi netti lato vendita al netto di IVA e fee.
    - sell_price_gross / (1+vat)
    - meno referral fee (fixed se presente, altrimenti pct * lordo)
    - meno fba_fee (se FBA) o shipping_fbm (se FBM)
    - meno altri costi
    """
    if sell_price_gross is None or (isinstance(sell_price_gross, float) and math.isnan(sell_price_gross)):
        return np.nan
    net_ex_vat = sell_price_gross / (1.0 + float(vat_sell))

    fee_ref = 0.0
    if referral_fee_fixed is not None and not (isinstance(referral_fee_fixed, float) and math.isnan(referral_fee_fixed)):
        fee_ref = float(referral_fee_fixed)
    elif referral_fee_pct is not None and not (isinstance(referral_fee_pct, float) and math.isnan(referral_fee_pct)):
        fee_ref = float(referral_fee_pct) * float(sell_price_gross)

    fee_fba = float(fba_fee) if fba_fee not in (None, np.nan) else 0.0

    return net_ex_vat - fee_ref - fee_fba - float(shipping_fbm) - float(other_costs_sell)