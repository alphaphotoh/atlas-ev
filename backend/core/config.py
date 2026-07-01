from dotenv import load_dotenv
import os

load_dotenv()

ORS_API_KEY = os.getenv("ORS_API_KEY")

if not ORS_API_KEY:
    raise Exception("ORS_API_KEY not found in .env")