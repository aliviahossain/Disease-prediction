import os
import sys

# Run from the repository root regardless of where this script is launched.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from dotenv import load_dotenv

# Load the file
load_dotenv()

# Check for the key
key = os.getenv("GEMINI_API_KEY")

if key:
    print("✅ SUCCESS: Found key starting with:", key[:5] + "...")
else:
    print("❌ ERROR: No key found. Python cannot see the .env file.")
