import os
import sys

# Run from the repository root regardless of where this script is launched.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from backend import create_app, db
from backend.models.disease import Disease

app = create_app()


def seed():
    df = pd.read_csv("data/hospital_data.csv")

    with app.app_context():
        # Rebuild ONLY the diseases table. Never db.drop_all(): that would
        # also erase user accounts, passwords and prediction history.
        Disease.__table__.drop(db.engine, checkfirst=True)
        Disease.__table__.create(db.engine)

        for _, row in df.iterrows():
            disease = Disease(
                disease=row["Disease"],
                prevalence=row["Prevalence"],
                sensitivity=row["Sensitivity"],
                false_positive=row["FalsePositive"],
            )
            db.session.add(disease)

        db.session.commit()
        print("✅ Diseases table populated successfully")


if __name__ == "__main__":
    seed()
