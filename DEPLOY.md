# Deployment Guide

## Option A: Render (simplest — one service handles everything)

1. Push to GitHub:
   ```
   git remote add origin https://github.com/YOUR_USERNAME/extraneta.git
   git push -u origin main
   ```

2. Go to https://render.com → New → Blueprint
3. Connect your GitHub repo → select extraneta
4. Render auto-reads render.yaml and creates all services
5. Set these env vars manually in Render dashboard:
   - `MINIO_ENDPOINT`: `<your-r2-account-id>.r2.cloudflarestorage.com`
   - `MINIO_ACCESS_KEY`: `<r2-access-key>`
   - `MINIO_SECRET_KEY`: `<r2-secret-key>`
   - `FRONTEND_URL`: `https://your-render-frontend-url.onrender.com`

---

## Option B: Railway (backend) + Vercel (frontend)

### Backend on Railway

1. Install Railway CLI:
   ```
   npm install -g @railway/cli
   ```
2. From the repo root:
   ```
   railway login
   railway init   # select "Empty project"
   railway add --plugin postgresql
   railway add --plugin redis
   railway up --service backend
   ```
3. Set env vars in Railway dashboard (use .env.example as reference):
   - `SECRET_KEY` — generate a random 32+ char string
   - `ENVIRONMENT` — `production`
   - `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE`
   - `FRONTEND_URL` — your Vercel URL (set after frontend deploy)
   - `BACKEND_CORS_ORIGINS` — `["https://your-app.vercel.app"]`
4. Copy the backend URL from Railway dashboard (e.g. `https://extraneta-backend.up.railway.app`)

### Frontend on Vercel

1. Update `frontend/vercel.json`: replace `RAILWAY_BACKEND_URL` with your Railway backend URL
2. Commit and push the change
3. Install Vercel CLI and deploy:
   ```
   npm install -g vercel
   cd frontend
   vercel --prod
   ```
4. Go back to Railway dashboard and set `FRONTEND_URL` to your Vercel URL

---

## Cloudflare R2 (free file storage — required for uploads)

1. Go to https://dash.cloudflare.com → R2 → Create bucket → name: `extraneta-uploads`
2. R2 → Manage R2 API tokens → Create token (Object Read & Write)
3. Copy these values:
   - Account ID (from R2 overview page)
   - Access Key ID
   - Secret Access Key
4. Set these env vars in your deployment platform:
   ```
   MINIO_ENDPOINT=<account-id>.r2.cloudflarestorage.com
   MINIO_ACCESS_KEY=<access-key-id>
   MINIO_SECRET_KEY=<secret-access-key>
   MINIO_SECURE=true
   MINIO_BUCKET=extraneta-uploads
   ```

---

## Environment Variables Reference

All required variables are listed in `.env.example`.
Copy it and fill in production values — never commit the filled-in `.env` file.

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (auto-set by Railway/Render) |
| `REDIS_URL` | Redis connection string (auto-set by Railway/Render) |
| `SECRET_KEY` | JWT signing key — min 32 random chars |
| `ENVIRONMENT` | Set to `production` |
| `MINIO_ENDPOINT` | R2 endpoint: `<account-id>.r2.cloudflarestorage.com` |
| `MINIO_ACCESS_KEY` | R2 Access Key ID |
| `MINIO_SECRET_KEY` | R2 Secret Access Key |
| `MINIO_BUCKET` | `extraneta-uploads` |
| `MINIO_SECURE` | `true` |
| `FRONTEND_URL` | Your frontend URL (for CORS) |
| `BACKEND_CORS_ORIGINS` | JSON array of allowed origins |
