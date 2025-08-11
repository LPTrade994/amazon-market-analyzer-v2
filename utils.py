from __future__ import annotations

def apply_vat_discount_rules(price: float, vat: float, discount: float, country: str) -> float:
    """
    Calcolo NET ACQUISTO mantenendo le regole esistenti (INVARIATE).

    - Acquisto da estero (non IT): sconto su prezzo NETTO -> Net = Price/(1+VAT) * (1 - Discount)
    - Acquisto in Italia (IT): sconto calcolato sul lordo e poi sottratto al NET ->
        Net = Price/(1+VAT) - Price*Discount

    Parametri:
      price: prezzo lordo (iva inclusa) letto dal dataset
      vat: aliquota IVA del paese di ACQUISTO (es. 0.22)
      discount: sconto (0..1)
      country: codice paese (IT, DE, FR, ...)
    """
    if price is None:
        return 0.0
    country = (country or "").upper()
    vat = float(vat or 0.0)
    disc = float(discount or 0.0)
    if country == "IT":
        return (price / (1.0 + vat)) - (price * disc)
    # estero
    return (price / (1.0 + vat)) * (1.0 - disc)
