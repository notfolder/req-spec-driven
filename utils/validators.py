import pandas as pd
from typing import TYPE_CHECKING


# 以下の関数は、PandasのSeriesオブジェクトを前提としています。
def check_is_numeric(series: pd.Series) -> bool:
    """
    シリーズが数値データ（float, int）のみで構成されているかチェックする。
    """
    # NaN値は許容することが多いが、ここでは厳密に数値型をチェックする
    return pd.to_numeric(series, errors="coerce").notna().all()
