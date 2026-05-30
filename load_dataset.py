from backend.database.models import insert_resume
import pandas as pd
import sqlite3

# Clear table before inserting
conn = sqlite3.connect("recruitment.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM resumes")
conn.commit()
conn.close()

print("Old data cleared...")

# Load dataset
df = pd.read_csv("dataset/Resume/Resume.csv")

for _, row in df.iterrows():
    insert_resume(row["Resume_str"], "dataset")

print(f"Dataset loaded successfully: {len(df)} resumes inserted")