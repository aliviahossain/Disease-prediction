import sys
import os

# Ensure we are at the project root
sys.path.append(os.getcwd())

from backend import create_app, db
from backend.models.user import User

def delete_user(email):
    app = create_app()
    with app.app_context():
        # Find the user
        users = User.query.filter_by(email=email).all()
        
        if not users:
            print(f"❌ No user found with email: {email}")
            return

        print(f"🔍 Found {len(users)} user(s) with email: {email}")
        
        for user in users:
            print(f"   - Deleting User: ID={user.id}, Username={user.username}")
            db.session.delete(user)
        
        db.session.commit()
        print("✅ Deletion successful!")

if __name__ == "__main__":
    delete_user('test@example.com')
