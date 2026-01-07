"""
Database Engine and Session Management
========================================

CRITICAL: This module initializes the SQLAlchemy engine.
The engine MUST be created successfully for the application to function.

Failure Modes:
- If Config.DATABASE_URL is invalid: ConfigurationError from config.py
- If database is unreachable: Connection error logged, but engine created
- If engine creation fails: Application crashes immediately

Session Management:
- SessionLocal: Thread-safe session factory
- get_db(): FastAPI dependency for request-scoped sessions
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Import config (this will fail-fast if DATABASE_URL is missing)
from app.config import Config

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE ENGINE INITIALIZATION
# ============================================================================

logger.info("Initializing database engine...")

try:
    # Create SQLAlchemy engine with production-safe settings
    engine = create_engine(
        Config.DATABASE_URL,
        # Connection pool settings (adjust for AWS RDS)
        pool_size=5,                    # Max connections in pool
        max_overflow=10,                # Additional overflow connections
        pool_timeout=30,                # Seconds to wait for connection
        pool_recycle=3600,              # Recycle connections after 1 hour
        pool_pre_ping=True,             # Test connections before using
        
        # Echo SQL in development only
        echo=False,
        
        # Disable SQLAlchemy connection pooling for serverless (optional)
        # poolclass=NullPool,  # Un comment if using AWS Lambda
    )
    
    logger.info(f"✓ Database engine created successfully")
    logger.info(f"  - Pool size: 5")
    logger.info(f"  - Max overflow: 10")
    logger.info(f"  - Pool pre-ping: enabled")
    
except Exception as e:
    logger.critical("=" * 80)
    logger.critical("FATAL: Failed to create database engine")
    logger.critical("=" * 80)
    logger.critical(f"Error: {e}")
    logger.critical("")
    logger.critical("This is likely caused by:")
    logger.critical("  1. Invalid DATABASE_URL format")
    logger.critical("  2. Missing psycopg2 driver (pip install psycopg2-binary)")
    logger.critical("  3. Database server unreachable")
    logger.critical("")
    logger.critical("Cannot continue. Exiting.")
    logger.critical("=" * 80)
    raise

# ============================================================================
# SESSION FACTORY
# ============================================================================

# Create session factory bound to engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

logger.info("✓ Session factory initialized")

# ============================================================================
# FASTAPI DEPENDENCY
# ============================================================================

def get_db():
    """
    FastAPI dependency for database sessions.
    
    Yields:
        Session: SQLAlchemy database session
        
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Note:
        This dependency REQUIRES that `engine` was created successfully.
        If engine creation failed, the application would have already crashed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# CONNECTION TEST (Optional - Enable for debugging)
# ============================================================================

def test_database_connection():
    """
    Test database connectivity at startup.
    
    This is optional but recommended for production deployments.
    Helps catch connectivity issues early.
    """
    try:
        logger.info("Testing database connection...")
        with engine.connect() as connection:
            result = connection.execute("SELECT version();")
            version = result.fetchone()[0]
            logger.info(f"✓ Database connection successful")
            logger.info(f"  PostgreSQL version: {version[:50]}...")
            return True
    except Exception as e:
        logger.error("✗ Database connection test failed")
        logger.error(f"  Error: {e}")
        logger.error("  Note: Application will continue, but database operations will fail")
        return False


# Uncomment to test connection at startup:
# test_database_connection()
