import os
import sys
from dotenv import load_dotenv

# Add current dir to path
sys.path.append(os.getcwd())

load_dotenv()

try:
    from config import Config
    print(f"Config loaded. Backend URL: {Config.BACKEND_URL}")
except Exception as e:
    print(f"Error loading config: {e}")

try:
    from services.oauth import oauth
    print("OAuth registry imported.")
except Exception as e:
    print(f"Error importing oauth: {e}")

try:
    print("Attempting to create google client...")
    client = oauth.create_client('google')
    print(f"Google client: {client}")
except Exception as e:
    print(f"Error creating google client: {e}")

try:
    print("Attempting to create microsoft client...")
    client = oauth.create_client('microsoft')
    print(f"Microsoft client: {client}")
    print(f"Microsoft Client ID from Config: {Config.MICROSOFT_CLIENT_ID}")
except Exception as e:
    print(f"Error creating microsoft client: {e}")
