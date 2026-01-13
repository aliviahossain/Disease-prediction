from backend import create_app, db
from backend.models.prediction import PredictionHistory
from backend.models.user import User

app = create_app()

with app.app_context():
    print("Checking database...")
    user = User.query.first()
    if not user:
        print("No users found.")
    else:
        print(f"Checking history for user: {user.username} (ID: {user.id})")
        history = PredictionHistory.query.filter_by(user_id=user.id).all()
        print(f"Found {len(history)} records.")
        
        for item in history:
            print(f"ID: {item.id}")
            print(f"Created At Type: {type(item.created_at)}")
            print(f"Created At Value: {item.created_at}")
            print(f"Probability Type: {type(item.ml_probability)}")
            try:
                print(f"Formatted Date: {item.created_at.strftime('%Y-%m-%d')}")
            except Exception as e:
                print(f"Error formatting date: {e}")
            break # Just check the first one
