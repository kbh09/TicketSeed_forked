from pathlib import Path
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import RAW_DATA_PATH, PROCESSED_DATA_DIR

MULTI_VALUE_COLUMNS = [
    "actor",
    "director",
    "genre",
    "production_company",
    "distributor" ]

NUMERIC_COLUMN_TYPES = {
    "screen_national": "int",
    "sales_national": "int",
    "audience_national": "int",
    "production_year": "int",
    "running_time": "int",
    "comment_cgv": "int",
    "comment_naver": "int",
    "rate_naver": "float",
}

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

CODED_ENTITY_SPECS = {
    "actor": {
        "delimiter"  : "|",
        "code_prefix": "2",
        "code_column": "actor_code",
        "name_column": "actor_name" }
        ,
    "director": {
        "delimiter"  : "|",
        "code_prefix": "3",
        "code_column": "director_code",
        "name_column": "director_name" }}

NAMED_ENTITY_SPECS = {
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

#####################
#####################

def load_csv(path):
    df = pd.read_csv(path,encoding="utf-8-sig",dtype=str,keep_default_na=False)

    return df

def clean_column(df, columnList):
    result = df.copy()

    for column in columnList:
        result[column] = result[column].astype("string").str.strip().replace(["", "nan", "null", "none", "없음", "미상"],pd.NA)

    return result

def clean_numeric_columns(df):
    result = df.copy()

    for column, number_type in NUMERIC_COLUMN_TYPES.items():
        if column not in result.columns:
            continue

        values = result[column].astype("string").str.strip().str.replace(",", "", regex=False).replace(["", "nan", "null", "none", "없음", "미상"],pd.NA)

        result[column] = pd.to_numeric(values,errors="raise")

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

def add_role(df):
    actors = split_column(df,"actor","|","name")
    actors["role"] = "actor"

    directors = split_column(df,"director","|","name")
    directors["role"] = "director"

    all_people = pd.concat([actors, directors],ignore_index=True)

    people = all_people[["name"]].drop_duplicates().sort_values("name").reset_index(drop=True)

    people.insert(0,"person_id",range(1, len(people) + 1))

    movie_people = all_people.merge(people,on="name",how="left")

    movie_people = movie_people[["movie_code", "person_id", "role"]].drop_duplicates()

    return people, movie_people

def add_code(df,source_column,delimiter,code_prefix,code_column,name_column):
    relation = split_column(df,source_column,delimiter,name_column)

    entity_table = relation[[name_column]].drop_duplicates().sort_values(name_column).reset_index(drop=True)

    entity_table.insert(0,code_column,
        [f"{code_prefix}{number:06d}" for number in range(1, len(entity_table) + 1)])

    relation_table = relation.merge(entity_table,on=name_column,how="left",validate="many_to_one")

    relation_table = relation_table[["movie_code", code_column]].drop_duplicates()

    return entity_table, relation_table


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

def preprocess(path: Path):
    df = load_csv(path)

    multi_columns = [
        "movie_name",
        "actor",
        "director",
        "genre",
        "production_company",
        "distributor" ]

    df = clean_column(df, multi_columns)
    df = clean_numeric_columns(df)

    movies = df.drop(columns=[*MULTI_VALUE_COLUMNS,*WEEKLY_COLUMNS],errors="ignore")

    people, movie_people = add_role(df)

    genres, movie_genres                             = add_name(df,"genre",**NAMED_ENTITY_SPECS["genre"])

    distributors, movie_distributors                 = add_name(df,"distributor",**NAMED_ENTITY_SPECS["distributor"])

    production_companies, movie_production_companies = add_name(df,"production_company",**NAMED_ENTITY_SPECS["production_company"])

    daily_boxoffice = create_daily_dict(df)

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

#####################
#####################

if __name__ == "__main__":
    tables = preprocess(RAW_DATA_PATH)
    save_tables(tables, PROCESSED_DATA_DIR)

    print(f"전처리 결과 저장 완료: {PROCESSED_DATA_DIR}")
