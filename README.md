# 프로젝트 구조

```
TicketSeed_forked/
├── app/
│   └── config.py			# 전역변수 선언
|   └── db.py				# 데이터베이스 파일(.db) 불러오기 기능 구현
|   └── [retrieve.py		# 데이터베이스 값을 조건에 맞게 분석 및 출력]  *예정*
|
├── data/
│	├── raw/				# 원본 CSV 파일 저장 위치
│	│	└── movies.csv
|	|
│   └── processed/			# 전처리된 CSV 파일 저장 위치
|       └── movies.csv						# 영화 기본 정보 테이블
|		└── daily_boxoffice.csv				# 1~10일차 박스오피스 데이터 병합 테이블
|       └── distributor.cs	v				# 배급사 칼럼
|       └── movie_distributor.csv			# 배급사 테이블
|       └── genres.csv						# 장르 칼럼
|       └── movie_genres.csv				# 장르 테이블
|       └── movie_people.csv				# 배우 및 감독 엔티티
|       └── people.csv						# 배우 및 감독 릴레이션
|       └── production_companies.csv		# 제작사 칼럼
|       └── movie_production_companies.csv	# 제작사 테이블
│
├── DB/						# 데이터베이스 생성 위치
│   └── movies.db   
│
└── pipeline/
    └── 00_dataCheck.py     # 데이터 칼럼 별 결측치, 중복값, 타입 확인
    └── 01_preprocess.py    # 데이터 전처리 및 타입 지정 후, csv로 저장
    └── 02_schema.py     	# CSV → SQLite DB 변환
```
