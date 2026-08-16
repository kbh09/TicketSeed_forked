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
    "distributor",
]

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
    df = pd.read_csv(path,encoding="utf-8-sig",dtype={"movie_code": "string"},keep_default_na=False)

    return df

def clean_column(df, columnList):
    result = df.copy()

    for column in columnList:
        result[column] = result[column].astype("string").str.strip().replace(["", "nan", "null", "none", "없음", "미상"],pd.NA)

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

# 다중값 외에도 단일값 컬럼도 전처리하는 함수를 추가.
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

    movies = df.drop(columns=MULTI_VALUE_COLUMNS,errors="ignore")

    actors, movie_actors             = add_code(df,"actor",**CODED_ENTITY_SPECS["actor"])

    directors, movie_directors       = add_code(df,"director",**CODED_ENTITY_SPECS["director"])

    genres, movie_genres             = add_name(df,"genre",**NAMED_ENTITY_SPECS["genre"])

    distributors, movie_distributors = add_name(df,"distributor",**NAMED_ENTITY_SPECS["distributor"])

    production_companies, movie_production_companies = add_name(df,"production_company",**NAMED_ENTITY_SPECS["production_company"])

    return {
        "movies"         : movies,
        "actors"         : actors,
        "movie_actors"   : movie_actors,
        "directors"      : directors,
        "movie_directors": movie_directors,
        "genres"         : genres,
        "movie_genres"   : movie_genres,
        "production_companies"      : production_companies,
        "movie_production_companies": movie_production_companies,
        "distributors"              : distributors,
        "movie_distributors"        : movie_distributors }

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
