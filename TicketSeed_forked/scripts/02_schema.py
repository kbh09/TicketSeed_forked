import csv
import sqlite3
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import PROCESSED_DATA_DIR, DB_PATH

# PK, FK 추론을 위한 칼럼 꼬리말 명시
TEXT_SUFFIXES = ("_code", "_name", "_date")

# 자동 추론하지 않는 복합 PK만 별도 지정
COMPOSITE_KEYS = {
    "movie_people"              : ["movie_code", "people_code", "role"],
    "movie_genres"              : ["movie_code", "genre_name"],
    "movie_distributors"        : ["movie_code", "distributor_name"],
    "movie_production_companies": ["movie_code","company_name"],
    "daily_boxoffice"           : ["movie_code", "week"] }


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        # load_tables()에서 에러 예방: columns가 None인 경우 ValueError 발생
        if reader.fieldnames is None:
            raise ValueError(f"CSV 파일에 컬럼명이 없습니다: {path}")

        return reader.fieldnames, list(reader)


# PK 검증(중복, NULL 여부)
def valid_key(rows, columns):
    if not rows:
        return False

    keys = []

    for row in rows:
        key = tuple(row[column] for column in columns)

        if any(value == "" for value in key):
            return False

        keys.append(key)

    return len(keys) == len(set(keys))


#칼럼 타입 확인
def infer_type(column, values):
    if column.endswith(TEXT_SUFFIXES):
        return "TEXT"

    values = [value for value in values if value != ""]

    if not values:
        return "TEXT"

    try:
        numbers = [float(value) for value in values]

        if all(number.is_integer() for number in numbers):
            return "INTEGER"

        return "REAL"

    except ValueError:
        return "TEXT"


# 각 테이블 값(칼럼, 행, 타입) 불러오기
def load_tables():
    tables = {}

    table_files = sorted(PROCESSED_DATA_DIR.glob("*.csv"))

    for table_file in table_files:
        table_name = table_file.stem
        columns, rows = read_csv(table_file)

        tables[table_name] = {
            "columns": columns,
            "rows": rows,
            "types": {column: infer_type(column,[row[column] for row in rows]) for column in columns }}

    return tables


# PK 찾기
def infer_primary_keys(tables):
    primary_keys = {}

    for table_name, table in tables.items():
        if table_name in COMPOSITE_KEYS:
            continue

        candidates = [[column] for column in table["columns"] if column.endswith("_code")]

        if not candidates:
            candidates = [[column] for column in table["columns"] if column.endswith("_name")]

        for candidate in candidates:
            if valid_key(table["rows"], candidate):
                primary_keys[table_name] = candidate
                break

        if table_name not in primary_keys:
            raise ValueError(f"{table_name}의 PK를 추론할 수 없습니다.")

    for table_name, columns in COMPOSITE_KEYS.items():
        if table_name not in tables:
            continue

        missing = [column for column in columns if column not in tables[table_name]["columns"]]

        if missing:
            raise ValueError(f"{table_name}의 복합 PK 컬럼이 없습니다: {missing}")

        if not valid_key(tables[table_name]["rows"], columns):
            raise ValueError(f"{table_name}의 복합 PK가 유효하지 않습니다.")

        primary_keys[table_name] = columns

    return primary_keys


# FK 찾기
def infer_foreign_keys(tables, primary_keys):
    for table_name in tables:
        if table_name not in primary_keys:
            raise ValueError(f"{table_name}에 PK가 없습니다.")

    parent_columns = {columns[0]: table_name for table_name, columns in primary_keys.items() if len(columns) == 1}

    foreign_keys = {}

    for table_name, table in tables.items():
        foreign_keys[table_name] = []

        for column in table["columns"]:
            parent_table = parent_columns.get(column)

            if parent_table is None:
                continue

            if parent_table == table_name:
                continue

            foreign_keys[table_name].append((column, parent_table))

    return foreign_keys


# SQL 구문 작성
def build_create_sql(table_name,table,primary_keys,foreign_keys):
    lines = []

    for column in table["columns"]:
        lines.append(f"{column} {table['types'][column]}")

    lines.append(f"PRIMARY KEY ({', '.join(primary_keys[table_name])})")

    for column, parent_table in foreign_keys[table_name]:
        lines.append(f"FOREIGN KEY ({column}) REFERENCES {parent_table}({column})")

    return (f"CREATE TABLE {table_name} ({",\n".join(lines)})")


# PK, FK 관계에 따라 생성 순서 부여
def get_table_order(tables, foreign_keys):
    pending = set(tables)
    order = []

    while pending:
        ready = [table_name for table_name in pending if all(parent_table not in pending for _, parent_table in foreign_keys[table_name])]

        if not ready:
            raise RuntimeError("테이블 생성 순서를 결정할 수 없습니다.")

        ready.sort()
        order.extend(ready)
        pending.difference_update(ready)

    return order


# 숫자는 타입 변환
def convert_value(value, column_type):
    if value == "":
        return None

    if column_type == "INTEGER":
        return int(float(value))

    if column_type == "REAL":
        return float(value)

    return value


# 데이터베이스 생성
def create_database(tables,primary_keys,foreign_keys,table_order):
    if DB_PATH.exists():
        print(f'{DB_PATH.name} deleted.')
        DB_PATH.unlink()

    DB_PATH.parent.mkdir(parents=True,exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    for table_name in table_order:
        table = tables[table_name]

        connection.execute(build_create_sql(table_name,table,primary_keys,foreign_keys))

        columns = table["columns"]
        placeholders = ", ".join("?" for _ in columns)

        values = []

        for row in table["rows"]:
            value = []

            for column in columns:
                value.append(convert_value(row[column],table["types"][column]))

            values.append(tuple(value))

        insert_sql = (f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})")

        connection.executemany(insert_sql, values)

    connection.commit()
    connection.close()

    return print(f'{DB_PATH.name} created at {DB_PATH.parent}.')


def main():
    tables = load_tables()

    primary_keys = infer_primary_keys(tables)

    foreign_keys = infer_foreign_keys(tables,primary_keys)

    table_order  = get_table_order(tables,foreign_keys)

    create_database(tables,primary_keys,foreign_keys,table_order)


if __name__ == "__main__":
    main()