# Deployment Steps: Strictly Dancing

Complete setup guide for deploying to Vercel (frontend) + Render (backend) + Supabase (database).

---

## Architecture Overview

| Component | Service | URL |
|-----------|---------|-----|
| Frontend | Vercel | `strictly-dancing.vercel.app` |
| Backend | Render | `strictly-dancing-api.onrender.com` |
| Database | Supabase | PostgreSQL with PostGIS |
| Cache | Render Redis | Free tier (25MB) |

---

## Step 1: Supabase Setup (Database)

### 1.1 Create Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in
3. Click **New Project**
4. Fill in:
   - **Name**: `strictly-dancing`
   - **Database Password**: Generate a strong password and **save it**
   - **Region**: Choose closest to your users
5. Click **Create new project**
6. Wait ~2 minutes for provisioning

### 1.2 Enable PostGIS Extension

1. In Supabase dashboard, go to **Database** → **Extensions**
2. Search for `postgis`
3. Click **Enable**
4. Schema: `extensions` (default)

### 1.3 Get Connection String

1. Go to **Project Settings** (gear icon) → **Database**
2. Scroll to **Connection string** section
3. Select **Session pooler** tab
4. Copy the connection string

**Format it for SQLAlchemy:**

Original:
```
postgres://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

Modified (add `ql+asyncpg` after `postgres`):
```
postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

**Save this connection string** — you'll need it for Render.

---

## Step 2: Render Setup (Backend)

### 2.1 Create Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub (recommended for easy repo access)

### 2.2 Deploy Using Blueprint

1. Click **New** → **Blueprint**
2. Connect your GitHub account if prompted
3. Select the `strictly-dancing` repository
4. Render will detect `render.yaml` in the repo root
5. Click **Apply**

This creates:
- Web service: `strictly-dancing-api`
- Redis instance: `strictly-dancing-redis`

### 2.3 Configure Environment Variables

1. Go to **Dashboard** → **strictly-dancing-api** → **Environment**
2. Add these variables:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres.[ref]:[pass]@...` | Your Supabase connection string |
| `JWT_SECRET_KEY` | (generate below) | For signing JWT tokens |

**Generate JWT_SECRET_KEY:**
```bash
openssl rand -hex 32
```

3. Click **Save Changes**

### 2.4 Note Service ID and Create API Key

**Get Service ID:**
1. Go to **strictly-dancing-api** → **Settings**
2. Scroll to **Service ID**
3. Copy it (format: `srv-xxxxxxxxxxxxxxxxxxxx`)

**Create API Key:**
1. Click your profile icon → **Account Settings**
2. Go to **API Keys**
3. Click **Create API Key**
4. Name: `github-actions`
5. Copy the key (you won't see it again)

### 2.5 Trigger First Deploy

1. Go to **strictly-dancing-api** → **Deploys**
2. Click **Manual Deploy** → **Deploy latest commit**
3. Watch the logs for any errors

---

## Step 3: Vercel Setup (Frontend)

### 3.1 Create Account

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub (recommended)

### 3.2 Import Project

1. Click **Add New** → **Project**
2. Select the `strictly-dancing` repository
3. Configure:
   - **Root Directory**: Click **Edit** → Enter `frontend` → **Continue**
   - **Framework Preset**: Vite (auto-detected)
   - **Build Command**: `bun run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)

### 3.3 Add Environment Variable

1. Expand **Environment Variables**
2. Add:

| Key | Value |
|-----|-------|
| `VITE_API_BASE_URL` | `https://strictly-dancing-api.onrender.com` |

3. Click **Deploy**

### 3.4 Verify Deployment

1. Wait for build to complete
2. Click the preview URL to test
3. Your production URL will be `https://strictly-dancing.vercel.app`

---

## Step 4: GitHub Secrets (Auto-Deploy)

### 4.1 Add Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

| Secret Name | Value |
|-------------|-------|
| `RENDER_API_KEY` | Your Render API key from Step 2.4 |
| `RENDER_SERVICE_ID` | Your Render service ID from Step 2.4 |

### 4.2 Test Auto-Deploy

1. Push a commit to `main` branch
2. Go to **Actions** tab in GitHub
3. Watch the **Deploy** workflow run
4. Verify both Vercel and Render deploy successfully

---

## Verification Checklist

After completing all steps, verify:

- [ ] **Backend Health**: https://strictly-dancing-api.onrender.com/health
  - Should return `{"status": "healthy"}`

- [ ] **API Docs**: https://strictly-dancing-api.onrender.com/docs
  - Should show Swagger UI

- [ ] **Frontend**: https://strictly-dancing.vercel.app
  - Should load the app

- [ ] **Registration Flow**: Try creating an account
  - Should complete without errors

---

## Free Tier Limits

| Service | Limit | Notes |
|---------|-------|-------|
| **Supabase** | 500MB database, 2GB bandwidth | Pauses after 1 week inactivity |
| **Render Web** | 750 hours/month | Sleeps after 15 min inactivity |
| **Render Redis** | 25MB | Sufficient for sessions/cache |
| **Vercel** | 100GB bandwidth | Generous for most apps |

**Important**: Free tier services sleep when inactive. First request after sleep takes 30-60 seconds to wake up.

---

## Troubleshooting

### Database Connection Issues

**Symptom**: Backend fails to start, database connection errors

**Solutions**:
1. Verify connection string uses `postgresql+asyncpg://` prefix
2. Use the **Session pooler** URL, not direct connection
3. Check if Supabase project is paused (wake it in dashboard)
4. Verify password doesn't have special characters that need URL encoding

### CORS Errors

**Symptom**: Frontend can't reach backend, CORS errors in console

**Solutions**:
1. Verify `https://strictly-dancing.vercel.app` is in backend CORS origins
2. Check for typos in the Vercel domain
3. Redeploy backend after CORS config changes

### Migration Failures

**Symptom**: Backend deploy fails during `alembic upgrade head`

**Solutions**:
1. Ensure PostGIS is enabled in Supabase
2. Check DATABASE_URL is correctly formatted
3. View Render logs for specific error message

### Redis Connection Issues

**Symptom**: Backend starts but caching/sessions fail

**Solutions**:
1. Verify Redis service is running in Render dashboard
2. Check REDIS_URL is automatically populated (from `fromService`)
3. Restart the web service after Redis is ready

---

## Useful Commands

**Generate new JWT secret:**
```bash
openssl rand -hex 32
```

**Test backend locally with production database:**
```bash
DATABASE_URL="postgresql+asyncpg://..." uvicorn app.main:app --reload
```

**Check Render deploy status via API:**
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys
```

---

## URLs Quick Reference

| Resource | URL |
|----------|-----|
| Frontend (Production) | https://strictly-dancing.vercel.app |
| Backend (Production) | https://strictly-dancing-api.onrender.com |
| API Documentation | https://strictly-dancing-api.onrender.com/docs |
| Health Check | https://strictly-dancing-api.onrender.com/health |
| Supabase Dashboard | https://supabase.com/dashboard |
| Render Dashboard | https://dashboard.render.com |
| Vercel Dashboard | https://vercel.com/dashboard |
