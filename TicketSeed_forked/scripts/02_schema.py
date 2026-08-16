import pandas as pd
import sys
from pathlib import Path
import sqlite3

# 이 파일은 pipeline/ 안에 있는데 app/config.py 를 가져다 쓴다.
# 파이썬은 "실행한 파일이 있는 폴더" 를 기준으로 모듈을 찾기 때문에,
# 프로젝트 뿌리를 검색 경로에 직접 넣어 줘야 한다
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import PROCESSED_DATA_DIR, DB_PATH

con = sqlite3.connect(DB_PATH)
con.execute("PRAGMA foreign_keys = ON")

TEXT_SUFFIXES = ("_code","_name","_date")

PRIMARY_KEYS = {
    "movies"                    : ["movie_code"],
    "people"                    : ["people_code"],
    "genres"                    : ["genre_name"],
    "distributors"              : ["distributor_name"],
    "production_companies"      : ["company_name"],
    "movie_people"              : ["movie_code","people_code","role"],
    "movie_genres"              : ["movie_code","genre_name"],
    "movie_distributors"        : ["movie_code","distributor_name"],
    "movie_production_companies": ["movie_code","company_name"],
    "daily_boxoffice"           : ["movie_code","week"]}

FOREIGN_KEYS = {
    "movie_people": [
      # (현재 테이블의 컬럼, 참조할 테이블, 참조할 컬럼)
        ("movie_code", "movies", "movie_code"),
        ("people_code", "people", "people_code")]
        ,
    "movie_genres": [
        ("movie_code", "movies", "movie_code"),
        ("genre_name", "genres", "genre_name")]
        ,
    "movie_distributors": [
        ("movie_code", "movies", "movie_code"),
        ("distributor_name","distributors","distributor_name")]
        ,
    "movie_production_companies": [
        ("movie_code", "movies", "movie_code"),
        ("company_name","production_companies","company_name")]
        ,
    "daily_boxoffice": [
        ("movie_code", "movies", "movie_code")]}


def infer_column_type(series):
    column_name = series.name

    if column_name.endswith(TEXT_SUFFIXES):
        return "TEXT"

    values = series.astype("string").replace("", pd.NA).dropna()

    if values.empty:
        return "TEXT"

    numbers = pd.to_numeric(values,errors="coerce")

    if numbers.isna().any():
        return "TEXT"

    if (numbers % 1 == 0).all():
        return "INTEGER"

    return "REAL"


def read_csv(path):
    return pd.read_csv(path,encoding="utf-8-sig",dtype=str,keep_default_na=False)

###

df = read_csv(PROCESSED_DATA_DIR)

column_types = {}

for column in df.columns:
    column_types[column] = infer_column_type(df[column])

###

def build_sql(table_name,df,column_types):
    lines = []

    for column in df.columns:
        column_type = column_types[column]
        lines.append(f"{column} {column_type}")

    primary_key = PRIMARY_KEYS.get(table_name)

    if primary_key:
        lines.append(f"PRIMARY KEY ({', '.join(primary_key)})")

    foreign_keys = FOREIGN_KEYS.get(table_name,[])

    for column, parent_table, parent_column in foreign_keys:
        lines.append(f"FOREIGN KEY ({column}) REFERENCES {parent_table}({parent_column})")

    return (f"CREATE TABLE {table_name} (\n"+ ",\n".join(lines)+ "\n)")

# Topological Sort Algorithm 
def get_order():
    dependencies = {}

    for table_name in PRIMARY_KEYS:
        dependencies[table_name] = set()

        for _, parent_table, _ in FOREIGN_KEYS.get(table_name,[]):
            dependencies[table_name].add(parent_table)

    table_order = []

    while dependencies:
        ready_tables = [table_name for table_name, parents in dependencies.items() if not parents]

        if not ready_tables:
            raise RuntimeError("테이블 간 참조 순서를 결정할 수 없습니다.")

        for table_name in ready_tables:
            table_order.append(table_name)
            del dependencies[table_name]

        for parents in dependencies.values():
            parents.difference_update(ready_tables)

    return table_order


# 테이블 생성 순서 지정을 위한 함수
def sort_by_dependency(tables):
  done = set() 
  order = [] 

  while len(order) < len(tables):
    moved = False
  
    for name, table in tables.items():
      if name in done:
        continue
     
      if all(owner in done for _, owner in table["fks"]):
        order.append(name)
        done.add(name)
        moved = True

    if not moved:
      order += [n for n in tables if n not in done]
      break

  return order