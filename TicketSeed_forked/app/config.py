from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   

PROCESSED_DATA_DIR = ROOT / "data/processed"

RAW_DATA_PATH   = ROOT / "data/raw/movies.csv"
DB_PATH         = ROOT / "DB/movie.db"