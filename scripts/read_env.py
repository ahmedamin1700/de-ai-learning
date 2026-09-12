from dotenv import load_dotenv
import os

load_dotenv()

env = os.getenv("APP_ENV")
print(f"Running in: {env}")
