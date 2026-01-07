import os
import sqlalchemy
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print(f"Connected to: {engine.url}")
print("Tables found in database:")
tables = inspector.get_table_names()
for t in tables:
    print(f" - {t}")
