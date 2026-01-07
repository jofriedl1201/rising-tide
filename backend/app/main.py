import os
import json
import stripe
from fastapi import FastAPI, Request, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import logging
from app.config import Config
from app.services.oauth import oauth
from app.routers import auth as auth_router
from app.dependencies import get_db

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.models import (
    Base,
    StripeEvent,
    EventStatusEnum,
    Tenant,
    StripeCustomer,
    TenantAppAccess,
    PlatformSubscription,
    SubscriptionStatusEnum,
    PlatformPlan,
    User,
    TenantMembership
)
from app.services.checkout import create_checkout_session, CheckoutServiceError

load_dotenv()

# --- CONFIGURATION ---
# --- CONFIGURATION ---
# Most config moved to config.py
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# --- DATABASE SETUP ---
from app.dependencies import engine
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
# Base.metadata.create_all(bind=engine) called below

app = FastAPI()

# ProxyHeadersMiddleware - CRITICAL for Cloudflare Tunnel
# Reads X-Forwarded-Proto header so Authlib generates HTTPS redirect URLs
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# Session Middleware (Required for Authlib)
# Session Middleware (Required for Authlib)
# backend is behind a proxy (Cloudflare), ensure cookies are Secure
# DEBUG: Relaxing https_only to debug session loss
app.add_middleware(
    SessionMiddleware, 
    secret_key=Config.SECRET_KEY,
    https_only=False, # Relaxed for debugging
    same_site='lax' 
)

# Include Auth Router
app.include_router(auth_router.router)

SIGNUP_HOSTS = ["signup.arisingtide.ai", "localhost:3000", "localhost:8000", "127.0.0.1:8000", "dame-commonwealth-dealers-wood.trycloudflare.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://www.risingtide.com", "https://signup.arisingtide.ai"] + [f"https://{host}" for host in SIGNUP_HOSTS if "localhost" not in host and "127.0.0.1" not in host] + [f"http://{host}" for host in SIGNUP_HOSTS if "localhost" in host or "127.0.0.1" in host],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def host_routing_middleware(request: Request, call_next):
    host = request.headers.get("host", "unknown")
    logger.info(f"Incoming Request Host: {host}")
    
    # Identify Context
    if host in SIGNUP_HOSTS:
        logger.info("Context: Signup/Billing Controller")
        request.state.context = "signup"
    else:
        logger.info(f"Context: Potential Tenant/App Logic (Host: {host})")
        request.state.context = "app"
        
    response = await call_next(request)
    return response

# Dependency
# Dependency imported from dependencies.py

# --- PYDANTIC MODELS ---
class CheckoutRequest(BaseModel):
    plan_id: int
    shop_name: str
    subdomain: str
    user_email: EmailStr

    user_email: EmailStr

# --- ENDPOINTS ---

# --- ENDPOINTS ---
# Auth endpoints moved to routers/auth.py

@app.post("/create-checkout-session")
def create_checkout_session_endpoint(request: CheckoutRequest, db: Session = Depends(get_db)):
    existing_tenant = db.query(Tenant).filter(Tenant.subdomain == request.subdomain).first()
    if existing_tenant:
        raise HTTPException(status_code=400, detail="Subdomain already exists")

    try:
        session = create_checkout_session(
            db=db,
            plan_id=request.plan_id,
            subdomain=request.subdomain,
            shop_name=request.shop_name,
            user_email=request.user_email
        )
        return {"sessionId": session.id, "url": session.url}
    except CheckoutServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def webhook_received(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Idempotency Check
    existing_event = db.query(StripeEvent).filter(StripeEvent.stripe_event_id == event['id']).first()
    if existing_event:
        if existing_event.status == EventStatusEnum.PROCESSED:
            return {"status": "success", "message": "Already processed"}
        # If FAILED or PENDING, we try again.
    else:
        new_event = StripeEvent(
            stripe_event_id=event['id'],
            event_type=event['type'],
            status=EventStatusEnum.PENDING,
            payload=json.loads(payload)
        )
        db.add(new_event)
        db.commit()

    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await handle_checkout_session_completed(db, session)
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            await handle_subscription_updated(db, subscription)

        # Mark as Processed
        # Refetch event to attach to session if needed (if session closed/commit)
        db_event = db.query(StripeEvent).filter(StripeEvent.stripe_event_id == event['id']).first()
        if db_event:
            db_event.status = EventStatusEnum.PROCESSED
            db.commit()

    except Exception as e:
        db.rollback() 
        db_event = db.query(StripeEvent).filter(StripeEvent.stripe_event_id == event['id']).first()
        if db_event:
            db_event.status = EventStatusEnum.FAILED
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success"}

async def handle_checkout_session_completed(db: Session, session: dict):
    # Parse Metadata
    metadata = session.get('metadata', {})
    subdomain = metadata.get('subdomain')
    shop_name = metadata.get('shop_name')
    user_email_meta = metadata.get('user_email')
    
    # Fallback to customer email if not in metadata
    if not user_email_meta:
        user_email_meta = session.get('customer_details', {}).get('email')

    if not subdomain:
        raise ValueError("Subdomain missing in metadata")

    # 1. Create Tenant
    tenant = db.query(Tenant).filter(Tenant.subdomain == subdomain).first()
    if not tenant:
        tenant = Tenant(subdomain=subdomain, name=shop_name)
        db.add(tenant)
        db.flush()

    # 2. Create User
    if user_email_meta:
        user = db.query(User).filter(User.email == user_email_meta).first()
        if not user:
            user = User(email=user_email_meta)
            db.add(user)
            db.flush()
            
        # 3. Link Tenant (Membership)
        membership = db.query(TenantMembership).filter(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == user.id
        ).first()
        
        if not membership:
            membership = TenantMembership(
                tenant_id=tenant.id,
                user_id=user.id,
                role="Owner"
            )
            db.add(membership)
    else:
        user = None # Should not happen typically if validation passed

    # 4. Stripe Map (StripeCustomer)
    stripe_customer_id = session.get('customer')
    if stripe_customer_id:
        customer = db.query(StripeCustomer).filter(StripeCustomer.stripe_customer_id == stripe_customer_id).first()
        if not customer:
            customer = StripeCustomer(
                stripe_customer_id=stripe_customer_id,
                tenant_id=tenant.id,
                billing_email=user_email_meta
            )
            if user:
                customer.user_id = user.id
            db.add(customer)
        else:
             customer.tenant_id = tenant.id
             if user: 
                 customer.user_id = user.id
        db.flush()
    else:
        customer = None # Should handle error

    # 5. Enable Access
    access = db.query(TenantAppAccess).filter(
        TenantAppAccess.tenant_id == tenant.id,
        TenantAppAccess.app_name == 'RAPID_CAT'
    ).first()
    
    if not access:
        access = TenantAppAccess(
            tenant_id=tenant.id,
            app_name='RAPID_CAT',
            is_active=True
        )
        db.add(access)

    # 6. Record Subscription
    subscription_id = session.get('subscription')
    if subscription_id and customer:
        plan_id_meta = metadata.get('plan_id')
        plan = None
        if plan_id_meta:
             plan = db.query(PlatformPlan).filter(PlatformPlan.id == int(plan_id_meta)).first()
        
        if plan:
             stripe_sub = stripe.Subscription.retrieve(subscription_id)
             sub_exists = db.query(PlatformSubscription).filter(PlatformSubscription.stripe_subscription_id == subscription_id).first()
             
             if not sub_exists:
                 new_sub = PlatformSubscription(
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer.id,
                    plan_id=plan.id,
                    status=SubscriptionStatusEnum.trialing,
                    current_period_start=cli_timestamp_to_datetime(stripe_sub['current_period_start']),
                    current_period_end=cli_timestamp_to_datetime(stripe_sub['current_period_end']),
                    trial_start=cli_timestamp_to_datetime(stripe_sub['trial_start']) if stripe_sub['trial_start'] else None,
                    trial_end=cli_timestamp_to_datetime(stripe_sub['trial_end']) if stripe_sub['trial_end'] else None
                )
                 db.add(new_sub)

from datetime import datetime
def cli_timestamp_to_datetime(ts):
    if ts:
        return datetime.fromtimestamp(ts)
    return None

async def handle_subscription_updated(db: Session, subscription: dict):
    stripe_sub_id = subscription.get('id')
    status = subscription.get('status')
    current_period_end = subscription.get('current_period_end')
    
    # 1. Update PlatformSubscription
    sub_record = db.query(PlatformSubscription).filter(
        PlatformSubscription.stripe_subscription_id == stripe_sub_id
    ).first()
    
    if not sub_record:
        # Warning log: Subscription not found?
        return

    sub_record.status = status
    sub_record.current_period_end = cli_timestamp_to_datetime(current_period_end)
    db.flush()
    
    # 2. Gatekeeper Check
    # Find TenantAppAccess via Customer -> Tenant
    # Need to load customer from subscription relation or query
    customer = db.query(StripeCustomer).filter(StripeCustomer.id == sub_record.stripe_customer_id).first()
    if not customer or not customer.tenant_id:
        return

    access = db.query(TenantAppAccess).filter(
        TenantAppAccess.tenant_id == customer.tenant_id,
        TenantAppAccess.app_name == 'RAPID_CAT'
    ).first()
    
    if not access:
        # Create default access row if missing?
        return

    if status in ['active', 'trialing']:
        access.is_active = True
    elif status in ['past_due', 'unpaid', 'canceled', 'incomplete_expired']:
        access.is_active = False
    
    db.add(access)
