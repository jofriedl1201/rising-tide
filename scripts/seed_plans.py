import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models import Base, PlatformPlan, AppNameEnum

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("DATABASE_URL not found in .env, using sqlite memory for demo or fail.")
    # For fail safety in this specific task context if env is missing (unlikely given previous steps)
    # DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_plans():
    db = SessionLocal()
    
    # Define Initial Plans
    # Note: Replace price_... with real Stripe Price IDs
    plans_data = [
        {
            "stripe_price_id": "price_1RapidCatProTrial", 
            "app_name": AppNameEnum.RAPID_CAT,
            "plan_tier": "PRO",
            "is_trial": True,
            "trial_days": 14,
            "features_config": {"max_projects": 100, "support": "priority"}
        },
        {
            "stripe_price_id": "price_1RapidCatBasic", 
            "app_name": AppNameEnum.RAPID_CAT,
            "plan_tier": "BASIC",
            "is_trial": False,
            "trial_days": 0,
            "features_config": {"max_projects": 5, "support": "standard"}
        }
    ]

    print("Seeding plans...")
    for plan_data in plans_data:
        # Check if exists
        exists = db.query(PlatformPlan).filter(
            PlatformPlan.stripe_price_id == plan_data["stripe_price_id"]
        ).first()

        if not exists:
            plan = PlatformPlan(**plan_data)
            db.add(plan)
            print(f"Adding plan: {plan_data['app_name']} - {plan_data['plan_tier']}")
        else:
            print(f"Plan already exists: {plan_data['app_name']} - {plan_data['plan_tier']}")

    db.commit()
    db.close()
    print("Seeding completed.")

if __name__ == "__main__":
    # Ensure tables exist (if running against fresh DB)
    Base.metadata.create_all(engine)
    seed_plans()
