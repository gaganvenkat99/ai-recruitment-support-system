import sqlite3
import os

# ==============================
# PATH SETUP
# ==============================
BASE_DIR = os.path.dirname(__file__)

DB_PATH = os.path.join(BASE_DIR, "backend", "database", "recruitment_fixed_ids.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "backend", "database", "schema.sql")

# ==============================
# CREATE DATABASE
# ==============================
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ==============================
# LOAD SCHEMA (ALL TABLES)
# ==============================
with open(SCHEMA_PATH, "r") as f:
    schema = f.read()
    cursor.executescript(schema)

conn.commit()
conn.close()

print("Database created successfully with all tables")