import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend import create_app, db
from backend.models.user import User

def verify_signup():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB for test
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing

    with app.app_context():
        db.create_all()
        client = app.test_client()

        # 1. Test GET request (Form display)
        print("Testing GET /signup...")
        response = client.get('/signup')
        if response.status_code == 200 and b'Sign Up' in response.data:
            print("✅ GET /signup successful")
        else:
            print(f"❌ GET /signup failed: {response.status_code}")
            return

        # 2. Test POST request (User creation)
        print("Testing POST /signup with new user...")
        response = client.post('/signup', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        if response.status_code == 200:
            # Check for success message
            if b'Account Created Successfully' in response.data:
                 print("✅ POST /signup (creation) successful - Message found")
            else:
                 print("⚠️ POST /signup successful but message not found found")
            
            # Verify user in DB
            user = User.query.filter_by(username='testuser').first()
            if user:
                print("✅ User found in database")
                print(f"   Matches: {user}")
                # Verify password hashing
                from flask_bcrypt import Bcrypt
                bcrypt = Bcrypt(app)
                if bcrypt.check_password_hash(user.password_hash, 'password123'):
                     print("✅ Password is securely hashed")
                else:
                     print("❌ Password hash verification failed")
            else:
                print("❌ User NOT found in database")
        else:
            print(f"❌ POST /signup failed: {response.status_code}")

        # 3. Test Duplicate User
        print("Testing POST /signup with duplicate user...")
        response = client.post('/signup', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
         
        if b'Username or Email already exists' in response.data:
            print("✅ Duplicate detection successful")
        else:
            print("❌ Duplicate detection failed")

if __name__ == "__main__":
    verify_signup()
