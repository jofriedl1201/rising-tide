from authlib.integrations.starlette_client import OAuth
from app.config import Config

oauth = OAuth()

# Google Registration
oauth.register(
    name='google',
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Microsoft Registration
# Manual configuration for Multi-Tenant apps (bypasses strict issuer validation)
oauth.register(
    name='microsoft',
    client_id=Config.MICROSOFT_CLIENT_ID,
    client_secret=Config.MICROSOFT_CLIENT_SECRET,
    # REMOVED: server_metadata_url (This prevents the strict validation rules from loading)
    
    # MANUAL CONFIGURATION (The "Multi-Tenant" Standard):
    access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
    authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    api_base_url='https://graph.microsoft.com/v1.0/',
    jwks_uri='https://login.microsoftonline.com/common/discovery/v2.0/keys',
    
    client_kwargs={
        'scope': 'openid email profile',
        'token_endpoint_auth_method': 'client_secret_post',
    }
)

