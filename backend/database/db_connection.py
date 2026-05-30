import sqlite3

DB_PATH = "recruitment_fixed_ids.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn
