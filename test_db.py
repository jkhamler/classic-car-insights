import os
from dotenv import load_dotenv

load_dotenv()
print("API Key:", os.getenv("OLD_CARS_API_KEY"))