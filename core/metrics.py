from __future__ import annotations
import numpy as np
import pandas as pd

# Punteggio semplice per ranking opportunità (personalizzabile dalla UI)
def compute_score(df: pd.DataFrame,
                  w_margin: float = 0.5,
                  w_roi: float = 0.3,
                  w_demand: float = 0.2,
                  demand_cols: list[str] | None = None) -> pd.Series:
    demand_cols = demand_cols or ["Drops last 30 days", "Sales Rank: Current"]

    # Normalizzazioni robuste
    margin = df.get("Unit_Margin€", pd.Series([np.nan]*len(df))).astype(float)
    roi = df.get("ROI", pd.Series([np.nan]*len(df))).astype(float)

    m_z = (margin - np.nanmean(margin)) / (np.nanstd(margin) + 1e-9)
    r_z = (roi - np.nanmean(roi)) / (np.nanstd(roi) + 1e-9)

    # domanda: maggiore è meglio, ma per rank minore è meglio → invertiamo se col contiene "Rank"
    d_parts = []
    for c in demand_cols:
        if c not in df.columns:
            continue
        v = pd.to_numeric(df[c], errors='coerce')
        if "rank" in c.lower():
            v = -v
        z = (v - np.nanmean(v)) / (np.nanstd(v) + 1e-9)
        d_parts.append(z)
    d = np.nanmean(d_parts, axis=0) if d_parts else pd.Series([0]*len(df))

    score = w_margin*m_z + w_roi*r_z + w_demand*d
    return score