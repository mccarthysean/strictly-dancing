# Deployment Guide

## Architecture

| Service | Platform | URL |
|---------|----------|-----|
| Frontend | Vercel | `strictly-dancing.vercel.app` |
| Backend | Render | `strictly-dancing-api.onrender.com` |
| Database | Supabase | PostgreSQL with PostGIS |
| Cache | Render Redis | Free tier |

---

## 1. Supabase Setup (Database)

### Create Project
1. Go to [supabase.com](https://supabase.com) and create account
2. Click "New Project"
3. Choose organization and region (pick closest to your users)
4. Set database password (save this!)
5. Wait for project to provision (~2 minutes)

### Enable PostGIS Extension
1. Go to **Database** → **Extensions** in sidebar
2. Search for `postgis`
3. Click **Enable**
4. Select schema: `extensions` (default)

### Get Connection String
1. Go to **Project Settings** → **Database**
2. Find "Connection string" section
3. Copy the **Session pooler** connection string
4. Format: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`

**Important for SQLAlchemy:**
- Change `postgres://` to `postgresql://` if needed
- Add `+asyncpg` for async driver: `postgresql+asyncpg://...`

Example:
```
postgresql+asyncpg://postgres.abcdef123456:YourPassword@aws-0-us-west-1.pooler.supabase.com:5432/postgres
```

---

## 2. Render Setup (Backend)

### Create Account & Connect Repo
1. Go to [render.com](https://render.com) and create account
2. Click **New** → **Blueprint**
3. Connect your GitHub repository
4. Select `render.yaml` from repo root

### Configure Environment Variables
In Render Dashboard → Service → Environment:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Supabase pooler connection string |
| `JWT_SECRET_KEY` | Generate: `openssl rand -hex 32` |
| `DEBUG` | `false` |

### Deploy
1. Render will auto-deploy on push to `main`
2. First deploy runs database migrations automatically
3. Check logs for any errors

---

## 3. Vercel Setup (Frontend)

### Connect Repository
1. Go to [vercel.com](https://vercel.com) and create account
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Set **Root Directory** to `frontend`
5. Framework: `Vite` (auto-detected)

### Environment Variables
Add in Vercel Dashboard → Settings → Environment Variables:

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | `https://strictly-dancing-api.onrender.com` |

### Deploy
- Vercel auto-deploys on every push to `main`
- Preview deployments for every PR

---

## 4. GitHub Secrets

Add these secrets in GitHub → Settings → Secrets → Actions:

| Secret | Source |
|--------|--------|
| `RENDER_API_KEY` | Render Dashboard → Account → API Keys |
| `RENDER_SERVICE_ID` | Render Dashboard → Service → Settings → ID |

---

## Running Migrations

Migrations run automatically on Render deploy via the Dockerfile CMD.

To run manually:
```bash
# SSH into Render service or use Render Shell
alembic upgrade head
```

---

## Free Tier Limits

| Service | Limit | Note |
|---------|-------|------|
| Supabase | 500MB database, 2GB bandwidth | Pauses after 1 week inactivity |
| Render | 750 hours/month | Sleeps after 15min inactivity |
| Render Redis | 25MB | |
| Vercel | 100GB bandwidth | |

**Note:** Free tier services sleep when inactive. First request after sleep takes 30-60 seconds.

---

## Troubleshooting

### Database Connection Issues
- Ensure using `postgresql+asyncpg://` prefix
- Use pooler connection string, not direct connection
- Check Supabase project isn't paused (wake it in dashboard)

### CORS Errors
- Verify frontend URL in `backend/app/core/config.py` cors_origins
- Check Vercel deployment URL matches

### Migration Failures
- Check Supabase has PostGIS enabled
- Verify DATABASE_URL is correct
- Check Render logs for specific error
