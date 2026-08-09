# Backend Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the ChatGPT Clone backend to cloud platforms.

## Prerequisites

- GitHub repository connected
- API keys ready (OpenRouter, Tavily)
- Frontend deployed (for CORS configuration)

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Variables](#environment-variables)
3. [Deployment Options](#deployment-options)
   - [Option 1: Render](#option-1-render)
   - [Option 2: Railway](#option-2-railway)
4. [Post-Deployment Testing](#post-deployment-testing)
5. [Production Best Practices](#production-best-practices)

---

## Pre-Deployment Checklist

### ✅ Files Verified

- [x] `backend/requirements.txt` - All dependencies listed
- [x] `backend/.env` - Environment variables configured (not committed)
- [x] `backend/.env.example` - Template for environment variables
- [x] `.gitignore` - Excludes `.env`, `*.db`, `node_modules/`
- [x] `app/main.py` - Entry point configured
- [x] `app/database/database.py` - SQLite configuration ready

### ✅ Dependencies Verified

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
pydantic-settings==2.5.2
sqlalchemy==2.0.35
aiosqlite==0.20.0
httpx==0.27.2
python-dotenv==1.0.1
langchain==0.3.26
langchain-openai==0.3.21
PyJWT
passlib
bcrypt
email-validator
```

---

## Environment Variables

### Required Variables

```env
# Database
SQLITE_DATABASE_URL=sqlite:///./chatgpt_clone.db

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-very-secure-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256

# API Keys
OPENROUTER_API_KEY=sk-or-v1-your-actual-openrouter-key
TAVILY_API_KEY=tvly-dev-your-actual-tavily-key

# CORS (Update with your frontend domain)
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com

# Application
APP_NAME=ChatGPT Clone Backend
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=False
API_PREFIX=/api
```

### Important Notes

- **Never commit `.env` file** - It's already in `.gitignore`
- **Use strong SECRET_KEY** - Minimum 32 characters, random string
- **Set DEBUG=False** in production
- **Update ALLOWED_ORIGINS** with actual frontend domain (no wildcards)

---

## Deployment Options

### Option 1: Render

#### Step 1: Prepare Repository

1. Push code to GitHub
2. Ensure `.gitignore` includes `.env` and `*.db`
3. Verify `requirements.txt` is in `backend/` folder

#### Step 2: Create Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:

**Basic Settings:**
- **Name**: `chatgpt-clone-backend`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your default branch)
- **Root Directory**: `backend`
- **Runtime**: `Python 3`
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

**Plan:**
- Free tier (for testing) or paid tier (for production)
- Free tier sleeps after 15 minutes of inactivity

#### Step 3: Add Environment Variables

In Render Dashboard → Your Service → Environment:

```env
SQLITE_DATABASE_URL=sqlite:///./chatgpt_clone.db
SECRET_KEY=your-very-secure-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
OPENROUTER_API_KEY=sk-or-v1-your-actual-openrouter-key
TAVILY_API_KEY=tvly-dev-your-actual-tavily-key
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
APP_NAME=ChatGPT Clone Backend
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=False
API_PREFIX=/api
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-20b
```

#### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for build to complete (2-3 minutes)
3. Your API will be available at: `https://your-service-name.onrender.com`

#### Step 5: Verify Deployment

```bash
# Health check
curl https://your-service-name.onrender.com/health

# Expected response:
# {"status":"healthy","service":"ChatGPT Clone Backend","version":"1.0.0"}
```

---

### Option 2: Railway

#### Step 1: Prepare Repository

1. Push code to GitHub
2. Ensure `.gitignore` is properly configured

#### Step 2: Create Project on Railway

1. Go to [Railway Dashboard](https://railway.app/)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your repository

#### Step 3: Configure Service

1. Railway will auto-detect Python project
2. Set **Root Directory** to `backend`
3. Railway will use `requirements.txt` automatically

#### Step 4: Add Environment Variables

In Railway Dashboard → Your Project → Variables:

```env
SQLITE_DATABASE_URL=sqlite:///./chatgpt_clone.db
SECRET_KEY=your-very-secure-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
OPENROUTER_API_KEY=sk-or-v1-your-actual-openrouter-key
TAVILY_API_KEY=tvly-dev-your-actual-tavily-key
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
APP_NAME=ChatGPT Clone Backend
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=False
API_PREFIX=/api
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-20b
```

#### Step 5: Configure Start Command

In Railway Dashboard → Settings → Deploy:

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### Step 6: Deploy

1. Railway will automatically deploy
2. Wait for deployment to complete (2-3 minutes)
3. Your API will be available at: `https://your-project-name.up.railway.app`

#### Step 7: Verify Deployment

```bash
# Health check
curl https://your-project-name.up.railway.app/health

# Expected response:
# {"status":"healthy","service":"ChatGPT Clone Backend","version":"1.0.0"}
```

---

## Post-Deployment Testing

### 1. Health Check

```bash
curl https://your-backend-url.com/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "ChatGPT Clone Backend",
  "version": "1.0.0"
}
```

### 2. API Documentation

Visit: `https://your-backend-url.com/docs`

Should show FastAPI Swagger UI with all endpoints.

### 3. Test Authentication

#### Register User
```bash
curl -X POST "https://your-backend-url.com/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Expected:** User created successfully

#### Login
```bash
curl -X POST "https://your-backend-url.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Expected:** Returns `access_token`

### 4. Test Chat API

```bash
# Replace YOUR_TOKEN with actual token from login
curl -X POST "https://your-backend-url.com/api/v1/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?"
  }'
```

**Expected:** Streaming response with AI answer

### 5. Test Conversations API

```bash
# Get conversations
curl https://your-backend-url.com/api/v1/conversations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected:** JSON array of conversations

### 6. Test Feedback API

```bash
curl -X POST "https://your-backend-url.com/api/v1/feedback" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": 1,
    "rating": "positive",
    "comment": "Great response!"
  }'
```

**Expected:** Feedback saved successfully

---

## Production Best Practices

### 1. Security

- [ ] Use strong SECRET_KEY (minimum 32 characters, random)
- [ ] Set DEBUG=False
- [ ] Use HTTPS only (automatic on Render/Railway)
- [ ] Restrict ALLOWED_ORIGINS to specific domains
- [ ] Never expose API keys in frontend
- [ ] Regularly rotate API keys
- [ ] Enable CORS properly

### 2. Database

- [ ] SQLite database persists on Render/Railway
- [ ] Regular backups (download database periodically)
- [ ] Monitor database size
- [ ] For high traffic, consider PostgreSQL upgrade

### 3. Monitoring

- [ ] Check logs regularly in Render/Railway dashboard
- [ ] Monitor API response times
- [ ] Set up error alerts
- [ ] Track API usage (OpenRouter costs)

### 4. Performance

- [ ] Use production ASGI server (uvicorn with workers)
- [ ] Enable gzip compression
- [ ] Cache frequent queries
- [ ] Monitor memory usage

### 5. Cost Management

- [ ] Monitor OpenRouter API usage
- [ ] Monitor Tavily API usage
- [ ] Set usage alerts
- [ ] Use free tier for testing, paid for production

---

## Troubleshooting

### Issue: "Module not found" error

**Solution:** Ensure `Root Directory` is set to `backend` in deployment settings

### Issue: "Database is locked"

**Solution:** SQLite on Render/Railway should work fine. If issues occur, consider:
- Using connection pooling
- Switching to PostgreSQL

### Issue: "CORS error" in frontend

**Solution:** 
- Verify ALLOWED_ORIGINS includes your frontend domain
- Check that frontend is using correct backend URL
- Ensure no trailing slashes in CORS origins

### Issue: "Module 'app' has no attribute 'main'"

**Solution:** Verify start command is: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Issue: "Environment variable not found"

**Solution:** 
- Verify all environment variables are set in deployment platform
- Check for typos in variable names
- Ensure `.env` file is not being used (use platform's env vars)

### Issue: "Out of memory"

**Solution:**
- Upgrade to paid tier on Render/Railway
- Optimize database queries
- Reduce LLM context size

---

## Updating Deployment

### Render

1. Push changes to GitHub
2. Render will auto-deploy (if auto-deploy enabled)
3. Or manually trigger deploy in Render dashboard

### Railway

1. Push changes to GitHub
2. Railway will auto-deploy
3. Monitor deployment in Railway dashboard

---

## Custom Domain (Optional)

### Render

1. Go to Service → Settings → Custom Domains
2. Add your domain
3. Update DNS records as instructed
4. SSL certificate is automatic

### Railway

1. Go to Project → Settings → Domains
2. Add custom domain
3. Update DNS records
4. SSL certificate is automatic

---

## Monitoring and Logs

### Render

- View logs: Dashboard → Service → Logs
- Real-time logs available
- Can set up log drains

### Railway

- View logs: Project → Deployments → View Logs
- Real-time logs available
- Can set up logging integrations

---

## Backup Strategy

### SQLite Database Backup

Since SQLite is a file, backup is simple:

1. **Manual Backup:**
   ```bash
   # Download database file from deployment platform
   # Or use API to export data
   ```

2. **Automated Backup:**
   - Schedule periodic exports
   - Store backups in cloud storage (S3, GCS, etc.)
   - Keep last 7-30 days of backups

3. **Database Migration (Future):**
   - Consider PostgreSQL for production
   - Use Alembic for migrations
   - Export/import data as needed

---

## Cost Estimation

### Render Free Tier
- Free for testing
- Sleeps after 15 minutes inactivity
- 750 hours/month
- Limited bandwidth

### Render Paid Tier ($7/month)
- Always on
- No sleep
- Better performance

### Railway
- $5/month hobby plan
- $0.10/GB-hour after free tier
- Pay for what you use

### API Costs
- OpenRouter: Pay per token
- Tavily: Pay per search
- Monitor usage to control costs

---

## Support

- Render Docs: https://render.com/docs
- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- SQLAlchemy Docs: https://docs.sqlalchemy.org

---

## Summary

✅ Backend is deployment-ready
✅ All dependencies in requirements.txt
✅ Environment variables configured
✅ CORS configured for production
✅ Database configured for SQLite
✅ Multiple deployment options provided
✅ Testing checklist included
✅ Monitoring and backup strategies defined

Choose either Render or Railway and follow the steps above to deploy your backend!