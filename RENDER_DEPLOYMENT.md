# 🚀 1-Click Render Deployment Guide: LeadQualify AI

This repository is pre-configured with a **Render Blueprint (`render.yaml`)** for the fastest and easiest deployment possible.

---

## ⚡ Method 1: 1-Click Blueprint (Recommended & Fastest)

Render will automatically detect `render.yaml` and configure both the Python FastAPI backend and Next.js frontend with SSL, health checks, and automatic environment linking.

### Step 1: Open Render
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** in the top right, then select **Blueprint**.

### Step 2: Connect Your GitHub Repository
1. Select your connected GitHub account: **`Hunter28-lucky/Anaya-software-`**.
2. Click **Connect**.

### Step 3: Enter Your OpenRouter API Key
1. Render will show the two services to be created:
   - `leadqualify-backend` (Web Service, Python 3.10)
   - `leadqualify-frontend` (Web Service, Node 20)
2. In the `OPENROUTER_API_KEY` prompt, paste your key:
   ```text
   <your_openrouter_api_key>
   ```
3. Click **Apply**.

Render will now build both services and deploy them! Within 2–3 minutes, your frontend URL (`https://leadqualify-frontend.onrender.com`) and backend URL (`https://leadqualify-backend.onrender.com`) will be live.

---

## 🛠️ Method 2: Manual Web Service Setup (Alternative)

If you prefer creating the services individually:

### Backend Service:
- **Type**: Web Service
- **Name**: `leadqualify-backend`
- **Root Directory**: `backend`
- **Runtime**: `Python 3`
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `OPENROUTER_API_KEY`: `<your_openrouter_api_key>`
  - `OPENROUTER_MODEL`: `nvidia/nemotron-3-super-120b-a12b:free`
  - `DATABASE_URL`: `sqlite+aiosqlite:///./leadqualify.db`

### Frontend Service:
- **Type**: Web Service
- **Name**: `leadqualify-frontend`
- **Root Directory**: `frontend`
- **Runtime**: `Node`
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm start`
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: `https://leadqualify-backend.onrender.com` (use your actual backend Render URL)

---

## 💡 Troubleshooting & Notes

- **Spin-up Delay on Free Tier**: Render's free tier spins down services after 15 minutes of inactivity. The first request after sleep may take ~30 seconds to wake up.
- **Model Configured**: Powered by NVIDIA's 120-billion parameter Nemotron-3 (`nvidia/nemotron-3-super-120b-a12b:free`), delivering state-of-the-art enterprise classification at zero API cost.
- **Persistent Storage**: For multi-instance scaling in production, you can point `DATABASE_URL` to Supabase or Render Postgres using `postgresql+asyncpg://...`.
