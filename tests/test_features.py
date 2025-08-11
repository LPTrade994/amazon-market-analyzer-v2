import pandas as pd
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from core.features import _norm


def test_norm_coerces_strings_and_invalid():
    x = pd.Series(["1", "2", "bad", None])
    result = _norm(x, "0", "2")
    assert result.tolist() == [0.5, 1.0, 0.0, 0.0]


def test_norm_handles_invalid_scalars():
    assert _norm("bad", "0", "10") == 0.0
    assert _norm("5", "0", "10") == 0.5


def test_norm_handles_nan_bounds():
    x = pd.Series([5, 5])
    low = pd.Series([0, 0])
    high = pd.Series([10, float("nan")])
    result = _norm(x, low, high)
    assert result.tolist() == [0.5, 1.0]

    assert _norm(5, 0, float("nan")) == 1.0
    assert _norm(5, float("nan"), 10) == 0.5
