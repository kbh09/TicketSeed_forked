import pandas as pd
from collections import Counter

import sys
from pathlib import Path
from app.config import RAW_DATA_PATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ==========================================
# 1. CSV 불러오기
# ==========================================

df = pd.read_csv(RAW_DATA_PATH, encoding="utf-8-sig", dtype={"movie_code": "string"})

print(f"행 개수: {len(df):,}")
print(f"컬럼 개수: {len(df.columns):,}")
print()
print(df.isnull().sum())
print(df.info())
print()


# ==========================================
# 2. 컬럼별 기본 중복값 분석
# ==========================================

def analyze_column_duplicates(df):
    print("=" * 80)
    print("컬럼별 중복값 분석")
    print("=" * 80)

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
            f"중복={duplicate_count:,}"
        )

# ==========================================
# 4. 특정 컬럼에서 구분자로 분리했을 때
#    실제 고유값 분석
# ==========================================

def analyze_delimiter(column_name, separator="|"):

    print()
    print("=" * 80)
    print(f"컬럼 분석: {column_name}")
    print(f"구분자: '{separator}'")
    print("=" * 80)

    if column_name not in df.columns:
        print(f"컬럼 '{column_name}'이 존재하지 않습니다.")
        return

    values = df[column_name].dropna().astype(str)

    # 원본 셀 개수
    original_count = len(values)

    # 구분자로 분리
    split_values = []

    for value in values:
        parts = value.split(separator)

        for part in parts:
            part = part.strip()

            if part:
                split_values.append(part)

    # 빈도 계산
    counter = Counter(split_values)

    print(f"원본 셀 개수       : {original_count:,}")
    print(f"분리 후 전체 값 개수 : {len(split_values):,}")
    print(f"분리 후 고유값 개수  : {len(counter):,}")

    print()
    print("가장 많이 등장한 값 TOP 20")
    print("-" * 50)

    for value, count in counter.most_common(20):
        print(f"{count:6,}회 | {value}")


analyze_column_duplicates(df)