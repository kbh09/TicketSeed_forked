# 코드 설명

## 00_dataCheck.py

### 목적

- 데이터 전처리를 위해 원본 csv를 확인
- 다중값이 포함된 칼럼을 확인하고 데이터베이스 구조 설계

### 주요 모듈 및 매서드

- isnull().sum()                 : 결측치 확인
- info()                         : 결측치 및 타입 확인
- nunique()                      : 고유값 확인
- len(values) - values.nunique() : 중복값 확인

### 실행결과 및 계획

- 다중값으로 묶여있어 고유값과 중복값을 확인하기 어려움.
  - 장르의 경우에만, 고유값이 낮고 중복값이 낮아 유의미한 결과를 얻음.
- 다중값이 포함된 칼럼을 정규화 진행
  - 감독&배우, 배급사, 제작사, 장르별 테이블 구분
  - 감독과 배우는 한 테이블(people)로 병합하고 역할(role)과 고유코드값(people_code) 부여.
    - 코드, 이름을 포함한 엔티티 테이블 추가 생성
    - 감독과 배우가 같을 경우, 동명이인이 있을 경우를 대비

---

## 01_preprocess.py

### 목적

- 결측치 및 데이터베이스 생성을 위한 데이터 전처리 및 정규화

### 특징

- pandas 라이브러리 사용
  - 타입 확인, 다중값 분리, 데이터프레임 구조 등 전처리 과정에서 필수적인 기능이 포함되어있어 사용
- 다중값과 반복값을 정규화 및 정리
  - 개별 csv로 저장해서 전처리 과정을 직관적으로 볼 수 있게 함

### 로직

| 함수                                                               | 설명                                                                                           | parameter                                                                                                                                                                     | return                                                  |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| load_csv(path)                                                     | csv 불러오기                                                                                   | path = csv 파일 경로                                                                                                                                                          | pd.DataFrame                                            |
| normalize_values(series, remove_comma=False, remove_percent=False) | 결측치 제거 등의 전처리 기능 구현                                                              | series = 전처리할 칼럼 pd.Series<br />remove_comma = 콤마를 제거할 경우 True<br />remove_percent = 퍼센트 문자를 제거할 경우 True                                             | pd.Series                                               |
| clean_data(df, column_list)                                        | pd.to_numeric()), normalize_values() 등을 사용해 전처리 및 타입 지정                           | df = 전처리할 pd.DataFrame<br />column_list = df 내에서 전처리할 칼럼 List                                                                                                    | pd.DataFrame                                            |
| split_column(df,source_column,delimiter,name_column)               | 다중값을 각각 개별 행으로 분리 기능 구현                                                       | df = 다중값 컬럼이 포함된 pd.DataFrame<br />source_column = 다중값을 처리할 칼럼명 string<br />delimeter = 구분자 string<br />name_column = 분리한 값을 할당할 칼럼명 string | pd.DataFrame                                            |
| add_role(df,delimiter,name_column)                                 | 배우와 감독의 다중값을 합쳐서 분리하고 고유코드값(people_code)과 역할(role) 명시한 테이블 생성 | df = 사람 데이터(actor, director)가 들어있는 pd.DataFrame<br />delimeter = 구분자 string<br />name_column = 분리한 값을 할당할 칼럼명 string                                  | pd.DataFrame<br />(people 릴레이션,<br />people 엔티티) |
| add_name(df,source_column,delimiter,name_column)                   | 이름으로 구분할 다중값 분리 테이블 생성                                                        | df = 다중값 칼럼이 포함된 pd.DataFrame<br />source_column = 다중값 칼럼 명시 string<br />delimeter = 구분자 string<br />name_column = 분리한 값을 할당할 칼럼명 string       | pd.DataFrame<br />(릴레이션, 엔티티)                    |
| create_daily_dict(df)                                              | 1~10일차 박스오피스 데이터를 정리한 테이블 생성                                                | df = 해당 데이터가 포함된 pd.DataFrame                                                                                                                                        | pd.DataFrame                                            |
| preprocess(path)                                                   | 데이터 불러오기부터 데이터 테이블 생성까지 단계별로 실행                                       | path = csv 파일 경로                                                                                                                                                          | Dictionary                                              |
| save_tables(tables, output_dir)                                    | 생성된 데이터 테이블을 csv 형태로 저장                                                         | tables = 저장할 데이터테이블<br />output_dir = csv 파일을 저장할 경로                                                                                                         | -                                                       |

---

## 02_schema.py

### 목적

- SQLite 라이브러리를 통해 SQL 구문을 작성해 데이터베이스를 구성 및 생성

### 특징

- 수업 시간에 배운 코드를 최대한 활용 (01_schema.py)

### 로직

| 함수                                                          | 설명                                                 | parameter                                                                                                                                          | return                                       |
| ------------------------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| read_csv(path)                                                | csv 불러오기                                         | path = csv 파일 경로                                                                                                                               | Tuple, List<br />(칼럼명 Tuple, 레코드 List) |
| valid_key(rows, columns)                                      | PK 검증 기능 구현 (중복여부 및 Null 검사)            | rows = 행 데이터 값 List<br />columns = 칼럼명 Tuple                                                                                             | Bool                                         |
| infer_type(column, values)                                    | 칼럼의 타입 확인 및 지정                             | column = 확인할 칼럼 string<br />values = 해당 칼럼의 행 데이터 List                                                                               | "TEXT","INTEGER","REAL" 중 하나             |
| load_tables()                                                 | 각 테이블의 칼럼명, 레코드, 타입 불러오기           | -                                                                                                                                                  | Dictionary                                   |
| infer_primary_keys(tables)                                    | PK 찾기                                              | tables = PK를 찾을 테이블 Dictionary                                                                                                               | Dictionary                                   |
| infer_foreign_keys(tables, primary_keys)                      | FK 찾기                                              | tables = FK를 찾을 테이블 Dictionary<br />primary_keys = PK 매핑 Dictionary                                                                       | Dictionary                                   |
| build_create_sql(table_name,table,primary_keys,foreign_keys)  | SQL 구문 작성 기능 구현                              | table_name = 테이블 명 string<br />table = 해당 테이블 Dictionary<br />primary_keys = PK 매핑 Dictionary<br />foreign_keys = FK 매핑 Dictionary | List<br />(SQL 구문 string)                  |
| get_table_order(tables, foreign_keys)                         | PK FK 관계에 따른 테이블 생성 순서 지정              | tables = 테이블 Dictionary<br />foreign_keys = FK 매핑 Dictionary                                                                                | List                                         |
| convert_value(value, column_type)                             | SQL 데이터베이스 생성 시, 지정된 타입 할당 기능 구현 | value = 타입을 지정할 값 variable<br />column_type = 칼럼별로 지정한 타입 string                                                                   | None, int(), float(), string() 중 하나       |
| create_database(tables,primary_keys,foreign_keys,table_order) | SQL 데이터베이스 생성                                | tables = 테이블 Dictionary<br />primary_keys = PK 매핑 Dictionary<br />foreign_keys = FK 매핑 Dictionary<br />table_order = 생성 순서 List     | SQLite로 생성한 .db파일                      |
