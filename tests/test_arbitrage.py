import pandas as pd
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from core.arbitrage import attach_badges_for_pairs


def test_attach_badges_handles_string_inputs():
    df = pd.DataFrame([
        {
            "asin": "A1",
            "amazon_offer_availability_sell": "no amazon offer",
            "amazon_90d_oos_sell": "11",
            "buybox_pct_amz_90d_sell": "0.1",
            "total_offer_count_sell": "8",
        },
        {
            "asin": "A2",
            "amazon_offer_availability_sell": "",
            "amazon_90d_oos_sell": "5",
            "buybox_pct_amz_90d_sell": "0.5",
            "total_offer_count_sell": "12",
        },
        {
            "asin": "A3",
            "amazon_offer_availability_sell": "",
            "amazon_90d_oos_sell": "not numeric",
            "buybox_pct_amz_90d_sell": "NaN",
            "total_offer_count_sell": "unknown",
        },
    ])
    result = attach_badges_for_pairs(df)
    assert list(result["pair_badges"]) == [
        "No Amazon OOS90 Low%AMZ FewSellers",
        "",
        "Low%AMZ FewSellers",
    ]


def test_attach_badges_handles_missing_columns():
    df = pd.DataFrame([
        {"asin": "A1"},
        {"asin": "A2"},
    ])
    result = attach_badges_for_pairs(df)
    assert "pair_badges" in result.columns
    assert list(result["pair_badges"]) == ["", ""]
