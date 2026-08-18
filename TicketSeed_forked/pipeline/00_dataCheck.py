import pandas as pd
from collections import Counter

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import RAW_DATA_PATH


df = pd.read_csv(RAW_DATA_PATH, encoding="utf-8-sig", dtype={"movie_code": "string"})

print(f"행 개수: {len(df):,}")
print(f"컬럼 개수: {len(df.columns):,}")
print()
print(df.isnull().sum())
print(df.info())
print()

for column in df.columns:
    total = len(df)

    # 결측치 제외
    values = df[column].dropna()

    unique_count = values.nunique()
    duplicate_count = len(values) - unique_count

    print(
        f"{column:25} "
        f"전체={total:,} "
        f"값={len(values):,} "
        f"고유값={unique_count:,} "
        f"중복={duplicate_count:,}" )