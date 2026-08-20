import sqlite3
from app.config import DB_PATH
con = sqlite3.connect(DB_PATH)

def query(sql, params=()):
  return con.execute(sql, params).fetchall()


def one(sql, params=()):
  return con.execute(sql, params).fetchone()

def dicts(sql, params=()):
  cur = con.execute(sql, params)
  columns = [c[0] for c in cur.description]

  return [dict(zip(columns, row)) for row in cur.fetchall()]