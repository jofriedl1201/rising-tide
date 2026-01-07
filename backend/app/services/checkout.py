import os
import stripe
from app.models import (
    Tenant,
    PlatformPlan,
    StripeCustomer,
    User
)
from sqlalchemy.orm import Session

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class CheckoutServiceError(Exception):
    pass

def create_checkout_session(db: Session, plan_id: int, subdomain: str, shop_name: str, user_email: str):
    """
    Creates a Stripe Checkout Session for a subscription.

    Args:
        db: SQLAlchemy Session
        plan_id: The Database ID of the PlatformPlan
        subdomain: The subdomain for the shop/tenant
        shop_name: The name of the shop
        user_email: The user's email address

    Returns:
        The created Stripe Checkout Session object.
    """
    
    # 1. Lookup the plan
    plan = db.query(PlatformPlan).filter(PlatformPlan.id == plan_id).first()
    if not plan:
        raise CheckoutServiceError(f"Plan with id {plan_id} not found.")

    # 2. Configure Subscription Data (Trials)
    subscription_data = {}
    if plan.is_trial and plan.trial_days and plan.trial_days > 0:
        subscription_data["trial_period_days"] = plan.trial_days

    # 3. Construct Metadata
    # "Store the subdomain, shop_name, user_email, and internal plan_id"
    # Also keep app_name from previous requirement/logic
    metadata = {
        "subdomain": subdomain,
        "shop_name": shop_name,
        "user_email": user_email,
        "plan_id": str(plan.id),
        "app_name": plan.app_name.value if hasattr(plan.app_name, 'value') else plan.app_name,
        "plan_tier": plan.plan_tier
    }

    try:
        # 4. Create Stripe Session
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": plan.stripe_price_id, # Use price from plan
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=f"{frontend_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/cancel",
            customer_email=user_email,
            subscription_data=subscription_data if subscription_data else None,
            metadata=metadata,
        )
        return session

    except stripe.error.StripeError as e:
        raise CheckoutServiceError(f"Stripe error: {str(e)}")
