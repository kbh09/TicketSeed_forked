import sqlite3
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import DB_PATH


def print_separator(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def inspect_database(db_path):
    if not db_path.exists():
        print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return

    try:
        # 읽기 전용 연결
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        # 테이블 및 기타 객체 조회
        print_separator("DATABASE OBJECTS")

        cursor.execute("""
            SELECT type, name, tbl_name, sql
            FROM sqlite_master
            WHERE type IN ('table', 'index', 'view', 'trigger')
            ORDER BY type, name;
        """)

        objects = cursor.fetchall()

        for obj_type, name, table_name, sql in objects:
            print(f"\nType       : {obj_type}")
            print(f"Name       : {name}")
            print(f"Table Name : {table_name}")

            if sql:
                print("SQL:")
                print(sql)

        # 사용자 테이블 목록
        print_separator("TABLE LIST")

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)

        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            print("사용자 테이블이 없습니다.")
            return

        for table in tables:
            print(f"- {table}")

        # 각 테이블 상세 분석
        for table in tables:
            print_separator(f"TABLE: {table}")

            # 1. 컬럼 정보
            print("\n[Columns]")

            cursor.execute(f'PRAGMA table_info("{table}");')
            columns = cursor.fetchall()

            print(f"{'CID':<5} {'NAME':<25} {'TYPE':<15} {'NOT NULL':<10} "
                  f"{'DEFAULT':<20} {'PK'}")
            print("-" * 90)

            for cid, name, col_type, not_null, default_value, primary_key in columns:
                print(
                    f"{cid:<5} "
                    f"{name:<25} "
                    f"{str(col_type):<15} "
                    f"{not_null:<10} "
                    f"{str(default_value):<20} "
                    f"{primary_key}"
                )

            # 2. CREATE TABLE SQL
            print("\n[CREATE TABLE SQL]")

            cursor.execute("""
                SELECT sql
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = ?
            """, (table,))

            result = cursor.fetchone()

            if result and result[0]:
                print(result[0])

            # 3. 인덱스 정보
            print("\n[Indexes]")

            cursor.execute(f'PRAGMA index_list("{table}");')
            indexes = cursor.fetchall()

            if indexes:
                for index in indexes:
                    seq, index_name, unique, origin, partial = index

                    print(
                        f"Index: {index_name} | "
                        f"Unique: {bool(unique)} | "
                        f"Origin: {origin} | "
                        f"Partial: {bool(partial)}"
                    )

                    cursor.execute(f'PRAGMA index_info("{index_name}");')
                    index_columns = cursor.fetchall()

                    for _, _, column_name in index_columns:
                        print(f"  └─ Column: {column_name}")
            else:
                print("인덱스 없음")

            # 4. 외래 키 정보
            print("\n[Foreign Keys]")

            cursor.execute(f'PRAGMA foreign_key_list("{table}");')
            foreign_keys = cursor.fetchall()

            if foreign_keys:
                for fk in foreign_keys:
                    (
                        fk_id,
                        seq,
                        referenced_table,
                        from_column,
                        to_column,
                        on_update,
                        on_delete,
                        match
                    ) = fk

                    print(
                        f"{from_column} -> "
                        f"{referenced_table}.{to_column} "
                        f"(ON UPDATE: {on_update}, ON DELETE: {on_delete})"
                    )
            else:
                print("외래 키 없음")

            # 5. 전체 행 개수
            print("\n[Row Count]")

            cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
            row_count = cursor.fetchone()[0]

            print(f"Total Rows: {row_count}")

            # 6. 데이터 샘플
            print("\n[Sample Data - First 5 Rows]")

            cursor.execute(f'SELECT * FROM "{table}" LIMIT 5;')

            rows = cursor.fetchall()

            if rows:
                column_names = [description[0] for description in cursor.description]

                print(" | ".join(column_names))
                print("-" * 80)

                for row in rows:
                    print(" | ".join(str(value) for value in row))
            else:
                print("데이터 없음")

        # 데이터베이스 무결성 검사
        print_separator("INTEGRITY CHECK")

        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchall()

        for result in integrity_result:
            print(result[0])

    except sqlite3.DatabaseError as e:
        print(f"SQLite 데이터베이스 오류: {e}")

    except Exception as e:
        print(f"오류 발생: {e}")

    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    inspect_database(DB_PATH)