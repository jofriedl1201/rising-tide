from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.models import User
from app.services.oauth import oauth
from app.config import Config
from app.dependencies import get_db
import logging

# We need to import get_db from where it is defined or move it.
# Ideally, we refactor get_db to a dependencies module, but for now we will try to import from main 
# if main imports this router, we have a circular dep. 
# SOLUTION: We will define get_db here or assume dependencies.py exists. 
# For now, let's create a minimal dependencies.py in the next step or duplicate logic to avoid circular import.
# Actually, I'll create `dependencies.py` first in the previous turn if I could, but here I'll just rely on `main` to pass it? 
# No, router structure needs clean imports. 
# Workaround: local import inside function or create dependencies.py now.
# I will create dependencies.py in a separate tool call if it doesn't exist, but I cannot see it.
# Let's assume I will create dependencies.py.

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/auth/login/{provider}")
async def login(provider: str, request: Request, next: str = None):
    """
    Initiates the OAuth flow.
    Saves the 'next' redirect URL (e.g. acme.rapidcat.com) in a session cookie.
    """
    # Manually construct redirect_uri to prevent Authlib from guessing wrong protocol
    # CRITICAL: Must use BACKEND_URL from config (HTTPS) not auto-detected request URL (HTTP)
    redirect_uri = f"{Config.BACKEND_URL}/auth/callback/{provider}"
    
    # Allow overriding 'next' via query param
    if next:
        request.session['post_login_redirect'] = next

    logger.info(f"Initiating login for {provider} with redirect_uri: {redirect_uri}")
    logger.info(f"Current Session (Login Start): {request.session}")
    
    # Explicitly pass redirect_uri to authorize_redirect
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)


@router.get("/auth/callback/{provider}")
async def auth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    """
    Handles the callback from the provider.
    Exchanges code for token, looks up/creates user, sets session.
    """
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=400, detail="Invalid provider")
        
    try:
        logger.info(f"Callback received for {provider}")
        logger.info(f"Request Headers: {request.headers}")
        logger.info(f"Request Cookies: {request.cookies}")
        logger.info(f"Current Session (Callback Start): {request.session}")
        token = await client.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
            # Sometimes userinfo is in the token, sometimes via separate request
             user_info = await client.userinfo()
    except Exception as e:
        import traceback
        import sys
        
        # --- CRITICAL DEBUG LOGGING ---
        logger.error("="*60)
        logger.error("🛑 OAUTH CRITICAL FAILURE 🛑")
        logger.error(f"Exception Type: {type(e).__name__}")
        logger.error(f"Exception Message: {str(e)}")
        logger.error("--- Traceback ---")
        logger.error(traceback.format_exc())
        logger.error("--- Request Details ---")
        logger.error(f"Provider: {provider}")
        logger.error(f"Session State: {request.session.get('_state_google', 'NOT FOUND')}")
        logger.error(f"Incoming URL: {request.url}")
        logger.error("="*60)
        
        # Return the error visibly so we don't get a generic 404
        return RedirectResponse(url=f"{Config.FRONTEND_URL}/signup?error=auth_failed&details={str(e)}")

    email = user_info.get('email')
    if not email:
        return RedirectResponse(url=f"{Config.FRONTEND_URL}/signup?error=no_email")

    # Lookup User
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create "Global User"
        user = User(
            email=email,
            # Name, etc if available
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new global user: {email}")
    else:
        logger.info(f"Logged in existing user: {email}")

    # Set Session
    # We use starlette's session middleware which handles the cookie via request.session
    request.session['user_id'] = str(user.id)
    request.session['email'] = user.email
    
    # Determine Redirect
    # Read the post_login_redirect from session
    next_url = request.session.pop('post_login_redirect', None)
    
    # CRITICAL FIX: If next_url is a relative path, prepend FRONTEND_URL
    # This prevents redirect to backend domain (which returns 404)
    if next_url:
        if next_url.startswith('/'):
            # Relative path - prepend frontend URL
            next_url = f"{Config.FRONTEND_URL}{next_url}"
            logger.info(f"Converted relative redirect to: {next_url}")
    else:
        # Default redirect to frontend signup page
        next_url = f"{Config.FRONTEND_URL}/signup"
        logger.info(f"Using default redirect: {next_url}")
        
    return RedirectResponse(url=next_url)

@router.get("/users/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Returns the currently logged-in user based on the session cookie.
    """
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear() # Invalid session
        raise HTTPException(status_code=401, detail="User not found")
        
    return {
        "id": str(user.id),
        "email": user.email
    }
