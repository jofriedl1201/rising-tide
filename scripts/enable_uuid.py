from sqlalchemy import create_engine, text
from config import Config

engine = create_engine(Config.DATABASE_URL)

with engine.connect() as conn:
    # Enable the UUID extension
    conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
    conn.commit()
    print("✓ uuid-ossp extension has been enabled successfully!")
    
    # Verify
    result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'uuid-ossp';"))
    row = result.fetchone()
    if row:
        print("✓ Verification: uuid-ossp extension is now ACTIVE")
