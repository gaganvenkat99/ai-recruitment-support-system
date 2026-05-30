import pandas as pd
from database.models import insert_resume

def import_dataset(path):

    df = pd.read_csv(path)

    for _, row in df.iterrows():

        resume_text = row["Resume_str"]

        insert_resume(resume_text,"portal")

    print("Dataset imported successfully")