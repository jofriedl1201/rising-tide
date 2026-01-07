from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User
from config import Config

# Setup DB connection
engine = create_engine(Config.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("-" * 30)
print("INSPECTING USERS TABLE")
print("-" * 30)

users = db.query(User).all()

if not users:
    print("No users found in the database.")
else:
    for user in users:
        print(f"ID: {user.id} | Email: {user.email}")

print("-" * 30)
