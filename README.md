# Rising Tide - Production Deployment Structure

Clean, production-ready FastAPI backend for AWS EC2 deployment.

## Directory Structure

```
rising_tide/
├── backend/              # 🚀 DEPLOY THIS TO AWS EC2
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI entrypoint
│   │   ├── config.py       # Environment configuration
│   │   ├── models.py       # Database models
│   │   ├── dependencies.py # DB session management
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── auth.py     # OAuth endpoints
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── oauth.py    # OAuth providers
│   │       └── checkout.py # Stripe integration
│   └── requirements.txt
│
├── frontend/             # Deploy separately (Vercel/S3/nginx)
│   └── app/
│       ├── signup/
│       └── ...
│
├── scripts/              # Internal tools (NOT deployed)
│   ├── seed_plans.py
│   └── inspect_db.py
│
└── tests/                # Tests (NOT deployed)
    ├── test_api.py
    └── ...
```

## Backend Deployment to AWS EC2

### What to Deploy

**ONLY** the `backend/` directory:
```bash
# On your local machine
cd backend
zip -r backend.zip app/ requirements.txt
```

Upload `backend.zip` to EC2 and extract.

### Running on EC2

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run with gunicorn (production)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Systemd Service

Create `/etc/systemd/system/rising-tide.service`:

```ini
[Unit]
Description=Rising Tide API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/backend
Environment="PATH=/home/ubuntu/backend/venv/bin"
EnvironmentFile=/home/ubuntu/backend/.env
ExecStart=/home/ubuntu/backend/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

## Required Environment Variables

Create `/home/ubuntu/backend/.env` on EC2:

```bash
ENV=production
DATABASE_URL=postgresql+psycopg2://user:pass@rds.amazonaws.com:5432/db?sslmode=require
AUTH_BASE_URL=https://api.arisingtide.ai
SECRET_KEY=<generate with: openssl rand -hex 32>
BACKEND_URL=https://api.arisingtide.ai
FRONTEND_URL=https://auth.arisingtide.ai

# OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...

# Stripe (optional)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Running Locally

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from root .env or .env.local.backup)
# Set ENV=development and local URLs

# Run
uvicorn app.main:app --reload
```

Backend runs at: `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:3000`

## Deployment Checklist

### Before Deploying Backend

- [ ] Set all environment variables on EC2
- [ ] `DATABASE_URL` uses `postgresql+psycopg2://` with `?sslmode=require`
- [ ] `AUTH_BASE_URL` matches your production domain
- [ ] `SECRET_KEY` is randomly generated (not dev key)
- [ ] OAuth redirect URIs updated in Google/Microsoft consoles
- [ ] RDS security group allows EC2 instance

### EC2 Setup

```bash
# On EC2 instance
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv nginx

# Upload backend code
scp -i key.pem backend.zip ubuntu@ec2-ip:/home/ubuntu/
ssh -i key.pem ubuntu@ec2-ip

# Setup
cd /home/ubuntu
unzip backend.zip -d backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file with production variables
nano .env

# Test
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Setup systemd service (see above)
sudo systemctl daemon-reload
sudo systemctl enable rising-tide
sudo systemctl start rising-tide
```

### nginx Configuration

```nginx
server {
    listen 80;
    server_name api.arisingtide.ai;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then install SSL with certbot:
```bash
sudo certbot --nginx -d api.arisingtide.ai
```

## Environment-Based OAuth

OAuth redirect URIs are constructed from `AUTH_BASE_URL`:
- Development: `http://localhost:8000/auth/callback/google`
- Production: `https://api.arisingtide.ai/auth/callback/google`

Both must be registered in OAuth provider dashboards.

## Security

- ✅ `.env` files gitignored
- ✅ No secrets in code
- ✅ Fail-fast config validation
- ✅ SSL required in production
- ✅ OAuth state CSRF protection

## Testing

```bash
# Validate configuration
cd backend
python -c "from app.config import Config; print('✓')"

# Run tests
cd ..
pytest tests/

# Check imports
python -c "from backend.app.main import app; print('✓')"
```

## Troubleshooting

### "Module not found"

Run from backend/ directory:
```bash
cd backend
uvicorn app.main:app
```

### OAuth redirect mismatch

Ensure `AUTH_BASE_URL` in `.env` matches OAuth console redirect URI exactly.

### Database connection failed

Check `DATABASE_URL` format and RDS security group.

## Support

See deployment guides:
- `aws_deployment_plan.md` - Complete AWS setup
- `OAUTH_ENVIRONMENT_CONFIG.md` - OAuth configuration
- `database_config_hardening_guide.md` - Database setup
