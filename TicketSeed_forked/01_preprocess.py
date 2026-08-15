from pathlib import Path
import pandas as pd

###
# CONFIG 로 추후 분리
CSV_PATH = Path(__file__).resolve().parent / "movies.csv"


# 다중값 컬럼별 구분자입니다.
# 배우·감독은 |, 장르·제작사는 ,를 사용합니다.
MULTI_VALUE_DELIMITERS = {
    "actor": "|",
    "director": "|",
    "genre": ",",
    "distributor": ",",
    "production_company": ",",
}


# 배우와 감독만 코드를 부여합니다.
# 제작사와 장르는 이름 자체를 식별자로 사용합니다.
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

def clean_text(series: pd.Series) -> pd.Series:
    result = series.astype("string").str.strip()

    empty_values = {"", "nan", "null", "none", "없음", "미상"}
    empty_mask = (
        result.isna()
        | result.eq("")
        | result.str.lower().isin(empty_values)
    )

    return result.mask(empty_mask)


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(
                path,
                encoding="utf-8-sig",
                dtype={"movie_code": "string"},
                keep_default_na=False,
            )

    return df


def clean_multi_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    text_columns = [
        "movie_name",
        "actor",
        "director",
        "genre",
        "production_company",
        "distributor",
    ]

    for column in text_columns:
        if column in result.columns:
            result[column] = clean_text(result[column])

    return result


def split_multi_value_column(
    df: pd.DataFrame,
    source_column: str,
    delimiter: str,
    name_column: str,
) -> pd.DataFrame:
    
    relation = df[["movie_code", source_column]].copy()
    relation = relation.rename(
        columns={source_column: name_column}
    )

    relation[name_column] = (
        relation[name_column]
        .fillna("")
        .astype("string")
        .str.split(delimiter, regex=False)
    )

    relation = relation.explode(name_column)
    relation[name_column] = clean_text(relation[name_column])

    relation = relation.dropna(subset=[name_column])
    relation = relation.drop_duplicates(
        subset=["movie_code", name_column]
    )

    return relation.reset_index(drop=True)


def make_coded_entity_and_relation(
    df: pd.DataFrame,
    source_column: str,
    delimiter: str,
    code_prefix: str,
    code_column: str,
    name_column: str,
):
    relation = split_multi_value_column(
        df=df,
        source_column=source_column,
        delimiter=delimiter,
        name_column=name_column,
    )

    entity_table = (
        relation[[name_column]]
        .drop_duplicates()
        .sort_values(name_column)
        .reset_index(drop=True)
    )

    # 접두사 1자리와 순번 6자리로 7자리 코드를 생성합니다.
    entity_table.insert(
        0,
        code_column,
        [
            f"{code_prefix}{number:06d}"
            for number in range(1, len(entity_table) + 1)
        ],
    )

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


def make_named_entity_and_relation(
    df: pd.DataFrame,
    source_column: str,
    delimiter: str,
    name_column: str,
):

    relation = split_multi_value_column(
        df=df,
        source_column=source_column,
        delimiter=delimiter,
        name_column=name_column,
    )

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
    df = clean_multi_columns(df)

    actors, movie_actors = make_coded_entity_and_relation(
        df=df,
        source_column="actor",
        **CODED_ENTITY_SPECS["actor"],
    )

    directors, movie_directors = make_coded_entity_and_relation(
        df=df,
        source_column="director",
        **CODED_ENTITY_SPECS["director"],
    )

    genres, movie_genres = make_named_entity_and_relation(
        df=df,
        source_column="genre",
        **NAMED_ENTITY_SPECS["genre"],
    )

    distributors, movie_distributors = make_named_entity_and_relation(
        df=df,
        source_column="distributor",
        **NAMED_ENTITY_SPECS["distributor"],
    )

    production_companies, movie_production_companies = (
        make_named_entity_and_relation(
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
