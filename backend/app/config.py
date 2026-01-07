"""
Production-Hardened Configuration Module
===========================================

CRITICAL: This module controls database connectivity for the entire application.
Changes to this file must be reviewed for production safety.

Environment Variable Loading:
- Development: Loads from .env (optional fallback)
- Production: MUST have all variables in systemd/AWS environment
- Fails fast if critical variables are missing

Database URL Format (STRICT):
postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
"""

import os
import sys
import logging
from typing import Optional

# Configure logging BEFORE any other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Determine environment
ENV = os.getenv("ENV", "production")  # Default to production for safety
IS_PRODUCTION = ENV == "production"
IS_DEVELOPMENT = ENV == "development"

# Conditional .env loading (ONLY in development)
if IS_DEVELOPMENT:
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Look for .env in project root (two levels up from this file)
        # This file is at: backend/app/config.py
        # Project root is at: ../../
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Development mode: Loaded .env file from {env_file}")
        else:
            logger.warning(f"Development mode: .env file not found at {env_file}")
    except ImportError:
        logger.warning("python-dotenv not installed, continuing without .env")
else:
    logger.info(f"Production mode: Skipping .env file (ENV={ENV})")


class ConfigurationError(Exception):
    """
    Raised when critical configuration is missing or invalid.
    This exception should crash the application at startup.
    """
    pass


def _require_env_var(var_name: str, friendly_name: str = None) -> str:
    """
    Load a required environment variable with fail-fast behavior.
    
    Args:
        var_name: Environment variable name
        friendly_name: Human-readable description for error messages
        
    Returns:
        The environment variable value
        
    Raises:
        ConfigurationError: If the variable is missing or empty
    """
    value = os.getenv(var_name)
    
    if not value or value.strip() == "":
        friendly = friendly_name or var_name
        error_msg = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                   CRITICAL CONFIGURATION ERROR                        ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  Missing Required Environment Variable: {var_name:<30} ║
║                                                                        ║
║  Description: {friendly:<54} ║
║                                                                        ║
║  This application cannot start without this configuration.            ║
║                                                                        ║
║  AWS Deployment: Set this variable in your EC2:                       ║
║    - systemd service file                                             ║
║    - /etc/environment                                                 ║  
║    - Elastic Beanstalk environment properties                          ║
║                                                                        ║
║  Local Development: Add to your .env file                             ║
║    - Set ENV=development                                              ║
║    - Add {var_name}=<value>                                     ║
║                                                                        ║
╚══════════════════════════════════════════════════════════════════════╝
        """
        logger.error(error_msg)
        raise ConfigurationError(f"Missing required environment variable: {var_name}")
    
    return value.strip()


def _get_env_var(var_name: str, default: str = None, warn_if_missing: bool = False) -> Optional[str]:
    """
    Load an optional environment variable with logging.
    
    Args:
        var_name: Environment variable name
        default: Default value if not set
        warn_if_missing: Log a warning if missing
        
    Returns:
        The environment variable value or default
    """
    value = os.getenv(var_name, default)
    
    if not value and warn_if_missing:
        logger.warning(f"Optional environment variable {var_name} is not set, using default: {default}")
    
    return value


def _validate_database_url(url: str) -> None:
    """
    Validate the DATABASE_URL format.
    
    Args:
        url: Database connection string
        
    Raises:
        ConfigurationError: If the URL format is invalid
    """
    if not url.startswith("postgresql"):
        raise ConfigurationError(
            f"DATABASE_URL must start with 'postgresql' or 'postgresql+psycopg2'. "
            f"Got: {url[:50]}..."
        )
    
    if "://" not in url:
        raise ConfigurationError(
            f"DATABASE_URL appears invalid (missing '://'). "
            f"Expected format: postgresql+psycopg2://user:pass@host:port/db"
        )
    
    # Extract host for logging (without credentials)
    try:
        protocol_end = url.index("://")
        credentials_end = url.index("@", protocol_end)
        host_start = credentials_end + 1
        host_end = url.find("/", host_start)
        if host_end == -1:
            host_end = len(url)
        host = url[host_start:host_end]
        logger.info(f"✓ Database configuration loaded for host: {host}")
    except (ValueError, IndexError):
        logger.warning("Could not parse DATABASE_URL host for logging (format may be unusual)")


class Config:
    """
    Application Configuration (Production-Hardened)
    
    All critical configuration is loaded at import time.
    Missing variables will crash the application immediately.
    """
    
    # ============================================================================
    # CRITICAL: DATABASE CONFIGURATION
    # ============================================================================
    # This MUST be set in production. No fallbacks. No defaults.
    # Format: postgresql+psycopg2://user:pass@host:5432/dbname?sslmode=require
    
    DATABASE_URL = _require_env_var(
        "DATABASE_URL",
        "PostgreSQL connection string (AWS RDS)"
    )
    
    # Validate URL format
    _validate_database_url(DATABASE_URL)
    
    # ============================================================================
    # OAUTH BASE URL (Environment-Specific)
    # ============================================================================
    # This URL is used to construct OAuth redirect URIs dynamically
    # Development: http://localhost:8000
    # Production: https://api.arisingtide.ai
    
    AUTH_BASE_URL = _require_env_var(
        "AUTH_BASE_URL",
        "Base URL for OAuth redirects (e.g., https://api.arisingtide.ai)"
    )
    
    # Build the canonical OAuth redirect path
    # This MUST match what's registered with Google/Microsoft
    OAUTH_CALLBACK_PATH = "/auth/callback"  # Canonical path (no trailing slash)
    
    # Log OAuth configuration at startup
    logger.info(f"✓ OAuth redirect base: {AUTH_BASE_URL}")
    logger.info(f"  Google redirect: {AUTH_BASE_URL}{OAUTH_CALLBACK_PATH}/google")
    logger.info(f"  Microsoft redirect: {AUTH_BASE_URL}{OAUTH_CALLBACK_PATH}/microsoft")
    
    # ============================================================================
    # SECURITY
    # ============================================================================
    
    SECRET_KEY = _require_env_var(
        "SECRET_KEY",
        "Session encryption key (generate with: openssl rand -hex 32)"
    )
    
    # ============================================================================
    # APPLICATION URLS
    # ============================================================================
    
    BACKEND_URL = _require_env_var(
        "BACKEND_URL",
        "Public backend URL (e.g., https://api.arisingtide.ai)"
    )
    
    FRONTEND_URL = _require_env_var(
        "FRONTEND_URL",
        "Public frontend URL (e.g., https://auth.arisingtide.ai)"
    )
    
    BASE_URL = BACKEND_URL  # Alias for backward compatibility
    
    # ============================================================================
    # OAUTH PROVIDERS
    # ============================================================================
    
    GOOGLE_CLIENT_ID = _require_env_var(
        "GOOGLE_CLIENT_ID",
        "Google OAuth Client ID"
    )
    
    GOOGLE_CLIENT_SECRET = _require_env_var(
        "GOOGLE_CLIENT_SECRET",
        "Google OAuth Client Secret"
    )
    
    MICROSOFT_CLIENT_ID = _require_env_var(
        "MICROSOFT_CLIENT_ID",
        "Microsoft OAuth Client ID"
    )
    
    MICROSOFT_CLIENT_SECRET = _require_env_var(
        "MICROSOFT_CLIENT_SECRET",
        "Microsoft OAuth Client Secret"
    )
    
    # ============================================================================
    # OPTIONAL: STRIPE (with warnings)
    # ============================================================================
    
    STRIPE_SECRET_KEY = _get_env_var(
        "STRIPE_SECRET_KEY",
        warn_if_missing=True
    )
    
    STRIPE_WEBHOOK_SECRET = _get_env_var(
        "STRIPE_WEBHOOK_SECRET",
        warn_if_missing=True
    )


# ============================================================================
# STARTUP VALIDATION
# ============================================================================

logger.info("=" * 80)
logger.info("Configuration Module Loaded Successfully")
logger.info("=" * 80)
logger.info(f"Environment: {ENV}")
logger.info(f"Backend URL: {Config.BACKEND_URL}")
logger.info(f"Frontend URL: {Config.FRONTEND_URL}")
logger.info("=" * 80)

# This line will only execute if all required variables are present
# If any are missing, ConfigurationError will have been raised above
