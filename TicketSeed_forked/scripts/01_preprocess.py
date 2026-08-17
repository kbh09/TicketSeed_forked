from pathlib import Path
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import RAW_DATA_PATH, PROCESSED_DATA_DIR

# 다중값 컬럼 지정
MULTI_VALUE_COLUMNS = [
    "actor",
    "director",
    "genre",
    "production_company",
    "distributor" ]

# 숫자형 컬럼 지정
NUMERIC_COLUMN_TYPES = {
    "screen_national"   : "int",
    "sales_national"    : "int",
    "audience_national" : "int",
    "production_year"   : "int",
    "running_time"      : "int",
    "comment_cgv"       : "int",
    "comment_naver"     : "int",
    "rate_cgv"          : "float",
    "rate_naver"        : "float" }

# 일일 박스오피스 칼럼 지정
WEEKLY_COLUMNS = [
    "sales_01", "audience_01", "screen_01",
    "sales_02", "audience_02", "screen_02",
    "sales_03", "audience_03", "screen_03",
    "sales_04", "audience_04", "screen_04",
    "sales_05", "audience_05", "screen_05",
    "sales_06", "audience_06", "screen_06",
    "sales_07", "audience_07", "screen_07",
    "sales_08", "audience_08", "screen_08",
    "sales_09", "audience_09", "screen_09",
    "sales_10", "audience_10", "screen_10" ]

for column in WEEKLY_COLUMNS:
    NUMERIC_COLUMN_TYPES[column] = "int"

# 구분자, 분리할 칼럼 이름 지정
NAMED_ENTITY_SPECS = {
    "people": {
        "delimiter"     : "|",
        "name_column"   : "people_name" }
        ,
    "genre": {
        "delimiter"     : ",",
        "name_column"   : "genre_name" }
        ,
    "distributor": {
        "delimiter"     : ",",
        "name_column"   : "distributor_name" }
        ,
    "production_company": {
        "delimiter"     : ",",
        "name_column"   : "company_name" }}


def load_csv(path):
    df = pd.read_csv(path,encoding="utf-8-sig",dtype=str,keep_default_na=False)

    return df

def normalize_values(series, remove_comma=False, remove_percent=False):
    values = series.astype("string").str.strip().replace(["","nan","null","none","없음","미상"], pd.NA)

    if remove_comma:
        values = values.str.replace(",", "", regex=False)

    if remove_percent:
        values = values.str.replace("%", "", regex=False)

    return values


def clean_data(df, column_list):
    result = df.copy()

    for column in column_list:
        result[column] = normalize_values(result[column])

    for column, number_type in NUMERIC_COLUMN_TYPES.items():
        if column not in result.columns:
            continue

        values = normalize_values(result[column],remove_comma=True,remove_percent=(column == "rate_cgv"))

        result[column] = pd.to_numeric(values, errors="raise")

        if number_type == "int":
            result[column] = result[column].astype("Int64")
        else:
            result[column] = result[column].astype("Float64")

    return result


def split_column(df,source_column,delimiter,name_column):
    relation = df[["movie_code", source_column]].copy()

    relation = relation.rename(columns = {source_column:name_column})

    relation[name_column] = (relation[name_column].astype("string").str.split(delimiter, regex=False))

    relation = relation.explode(name_column)

    relation[name_column] = (relation[name_column].astype("string").str.strip())

    relation = relation[relation[name_column].notna() & relation[name_column].ne("")]

    # 한 영화 내의 동명이인은 고려되지 않음!
    relation = relation.drop_duplicates(subset=["movie_code", name_column])

    return relation.reset_index(drop=True)


# "NoReturn" is not iterable 에러 발생 -> return 값을 명시
def add_role(df,delimiter,name_column) -> tuple:
    actors = split_column(df,"actor",delimiter,name_column)
    actors["role"] = "actor"

    directors = split_column(df,"director",delimiter,name_column)
    directors["role"] = "director"

    all_people = pd.concat([actors, directors],ignore_index=True)

    people = all_people[["people_name"]].drop_duplicates().sort_values("people_name").reset_index(drop=True)

    people.insert(0,"people_code",[f"2{number:06d}" for number in range(1, len(people) + 1)])

    movie_people = all_people.merge(people,on="people_name",how="left")

    movie_people = movie_people[["movie_code", "people_code", "role"]].drop_duplicates()

    return people, movie_people


def add_name(df,source_column,delimiter,name_column):
    relation = split_column(df,source_column,delimiter,name_column)

    entity_table = relation[[name_column]].drop_duplicates().sort_values(name_column).reset_index(drop=True)

    relation_table = relation[["movie_code", name_column]].drop_duplicates()

    return entity_table, relation_table


def create_daily_dict(df):
    rows = []

    for week in range(1, 11):
        sales_column    = f"sales_{week:02d}"
        audience_column = f"audience_{week:02d}"
        screen_column   = f"screen_{week:02d}"

        for _, row in df.iterrows():
            sales    = row[sales_column]
            audience = row[audience_column]
            screens  = row[screen_column]

            rows.append({
                    "movie_code": row["movie_code"],
                    "week": week,
                    "sales": sales,
                    "audience": audience,
                    "screens": screens })

    return pd.DataFrame(rows,columns=["movie_code","week","sales","audience","screens"])


def preprocess(path):
    df = load_csv(path)

    multi_columns = [
        "movie_name",
        "actor",
        "director",
        "genre",
        "production_company",
        "distributor" ]
    
    clean_data(df, multi_columns)

    movies = df.drop(columns=[*MULTI_VALUE_COLUMNS,*WEEKLY_COLUMNS],errors="ignore")

    people, movie_people                             = add_role(df,**NAMED_ENTITY_SPECS["people"])

    genres, movie_genres                             = add_name(df,"genre",**NAMED_ENTITY_SPECS["genre"])

    distributors, movie_distributors                 = add_name(df,"distributor",**NAMED_ENTITY_SPECS["distributor"])

    production_companies, movie_production_companies = add_name(df,"production_company",**NAMED_ENTITY_SPECS["production_company"])

    daily_boxoffice                                  = create_daily_dict(df)

    return {
        "movies"                    : movies,
        "people"                    : people,
        "movie_people"              : movie_people,
        "genres"                    : genres,
        "movie_genres"              : movie_genres,
        "production_companies"      : production_companies,
        "movie_production_companies": movie_production_companies,
        "distributors"              : distributors,
        "movie_distributors"        : movie_distributors,
        "daily_boxoffice"           : daily_boxoffice }


def save_tables(tables, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    for table_name, table_df in tables.items():
        table_df.to_csv(output_dir / f"{table_name}.csv",index=False,encoding="utf-8-sig")


if __name__ == "__main__":
    tables = preprocess(RAW_DATA_PATH)
    save_tables(tables, PROCESSED_DATA_DIR)

    print(f"전처리 결과 저장 완료: {PROCESSED_DATA_DIR}")
