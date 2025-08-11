import pandas as pd
import numpy as np
from io import StringIO
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from core.loaders import load_many


def test_load_many_handles_invalid_ints():
    data = pd.DataFrame({
        "asin": ["A", "B"],
        "sales rank: current": [np.nan, "foo"],
    })
    buf = StringIO()
    data.to_csv(buf, index=False)
    buf.seek(0)
    buf.name = "test.csv"

    result = load_many([buf])
    assert result["sales_rank_current"].tolist() == [None, None]
