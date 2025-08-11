import pandas as pd
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from core.scoring_v2 import add_detectors

def test_add_detectors_handles_string_values():
    df = pd.DataFrame(
        {
            "amazon_90d_oos": ["11"],
            "score_demand": ["0.6"],
            "margin_pct": ["0.2"],
            "flipability_90d": ["85"],
            "buybox_std_90d": ["5"],
            "buybox_current": ["10"],
            "buybox_pct_amz_90d": ["0.1"],
            "total_offer_count": ["5"],
            "map_restriction": ["yes"],
            "return_rate": ["0.2"],
        }
    )
    result = add_detectors(df)
    assert result.loc[0, "badges"] == (
        "Window Advantage, Volatility Flip, Low Guarded Buybox, Risk Alert"
    )

def test_add_detectors_handles_missing_columns():
    df = pd.DataFrame({"map_restriction": ["no"]})
    result = add_detectors(df)
    assert result.loc[0, "badges"] == "Low Guarded Buybox"
