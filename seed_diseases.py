import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from backend import create_app, db
from backend.models.disease import Disease

app = create_app()

def seed():
    df = pd.read_csv("hospital_data.csv")

    with app.app_context():
        # Ensure tables are created in the ACTIVE database (MySQL)
        db.drop_all()
        db.create_all()

        for _, row in df.iterrows():
            disease = Disease(
                disease=row["Disease"],
                prevalence=row["Prevalence"],
                sensitivity=row["Sensitivity"],
                false_positive=row["FalsePositive"]
            )
            db.session.add(disease)

        db.session.commit()
        print("✅ Diseases table populated successfully (MySQL)")

if __name__ == "__main__":
    seed()
