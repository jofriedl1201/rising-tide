from sqlalchemy import create_engine, text
from config import Config

engine = create_engine(Config.DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'uuid-ossp';"))
    row = result.fetchone()
    
    if row:
        print("✓ uuid-ossp extension is ENABLED")
    else:
        print("✗ uuid-ossp extension is NOT enabled")
        print("\nTo enable it, run:")
        print("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
