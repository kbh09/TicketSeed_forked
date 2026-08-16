from pathlib import Path
import pandas as pd

###
# CONFIG 로 추후 분리
CSV_PATH = Path(__file__).resolve().parent / "data/movies.csv"

MULTI_VALUE_DELIMITERS = {
    "actor": "|",
    "director": "|",
    "genre": ",",
    "distributor": ",",
    "production_company": ",",
}

CODED_ENTITY_SPECS = {
    "actor": {
        "delimiter": "|",
        "code_prefix": "2",
        "code_column": "actor_code",
        "name_column": "actor_name",
    },
    "director": {
        "delimiter": "|",
        "code_prefix": "3",
        "code_column": "director_code",
        "name_column": "director_name",
    },
}

NAMED_ENTITY_SPECS = {
    "genre": {
        "delimiter": ",",
        "name_column": "genre_name"}
    ,
    "distributor": {
        "delimiter": ",",
        "name_column": "distributor_name"}
    ,
    "production_company": {
        "delimiter": ",",
        "name_column": "company_name"}
    ,
}
###

def load_csv(path):
    df = pd.read_csv(
                path,
                encoding="utf-8-sig",
                dtype={"movie_code": "string"},
                keep_default_na=False,
            )

    return df

def clean_column(df, columnList):
    result = df.copy()

    for column in columnList:
        result[column] = result[column].astype("string").str.strip().replace(["", "nan", "null", "none", "없음", "미상"],pd.NA)

    return result

def split_column(df,source_column,delimiter,name_column):
    relation = df[["movie_code", source_column]].copy()
    relation = relation.rename(
        columns={source_column: name_column}
    )

    relation[name_column] = (relation[name_column].astype("string").str.split(delimiter, regex=False))

    relation = relation.explode(name_column)

    relation = relation.dropna(subset=[name_column])
    relation = relation.drop_duplicates(
        subset=["movie_code", name_column]
    )

    return relation.reset_index(drop=True)


def add_code(df,source_column,delimiter,code_prefix,code_column,name_column):
    relation = split_column(df,source_column,delimiter,name_column)

    entity_table = (
        relation[[name_column]]
        .drop_duplicates()
        .sort_values(name_column)
        .reset_index(drop=True)
    )

    entity_table.insert(0,code_column,
        [f"{code_prefix}{number:06d}" for number in range(1, len(entity_table) + 1)])

    relation_table = relation.merge(
        entity_table,
        on=name_column,
        how="left",
        validate="many_to_one",
    )

    relation_table = relation_table[
        ["movie_code", code_column]
    ].drop_duplicates()

    return entity_table, relation_table


def add_name(df,source_column,delimiter,name_column):
    relation = split_column(df,source_column,delimiter,name_column)

    entity_table = (
        relation[[name_column]]
        .drop_duplicates()
        .sort_values(name_column)
        .reset_index(drop=True)
    )

    relation_table = relation[
        ["movie_code", name_column]
    ].drop_duplicates()

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
        "distributor",
    ]

    df = clean_column(df, multi_columns)

    actors, movie_actors = add_code(
        df=df,
        source_column="actor",
        **CODED_ENTITY_SPECS["actor"],
    )

    directors, movie_directors = add_code(
        df=df,
        source_column="director",
        **CODED_ENTITY_SPECS["director"],
    )

    genres, movie_genres = add_name(
        df=df,
        source_column="genre",
        **NAMED_ENTITY_SPECS["genre"],
    )

    distributors, movie_distributors = add_name(
        df=df,
        source_column="distributor",
        **NAMED_ENTITY_SPECS["distributor"],
    )

    production_companies, movie_production_companies = (
        add_name(
            df=df,
            source_column="production_company",
            **NAMED_ENTITY_SPECS["production_company"],
        )
    )

    return {
        "cleaned_df": df,
        "actors": actors,
        "movie_actors": movie_actors,
        "directors": directors,
        "movie_directors": movie_directors,
        "genres": genres,
        "movie_genres": movie_genres,
        "production_companies": production_companies,
        "movie_production_companies": movie_production_companies,
        "distributors": distributors,
        "movie_distributors": movie_distributors,
    }


if __name__ == "__main__":
    tables = preprocess(CSV_PATH)

    print("배우 테이블")
    print(tables["actors"].head())

    print("\n영화-배우 관계 테이블")
    print(tables["movie_actors"].head())

    print("\n감독 테이블")
    print(tables["directors"].head())

    print("\n장르 테이블")
    print(tables["genres"].head())

    print("\n제작사 테이블")
    print(tables["production_companies"].head())
