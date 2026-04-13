import os
from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("DB_URI")