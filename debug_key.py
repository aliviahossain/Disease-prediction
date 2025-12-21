import os
from dotenv import load_dotenv

# Load the file
load_dotenv()

# Check for the key
key = os.getenv("GEMINI_API_KEY")

if key:
    print("✅ SUCCESS: Found key starting with:", key[:5] + "...")
else:
    print("❌ ERROR: No key found. Python cannot see the .env file.")