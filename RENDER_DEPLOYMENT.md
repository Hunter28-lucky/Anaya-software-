# 🚀 1-Click Render Deployment Guide: LeadQualify AI

LeadQualify AI is packaged with a **multi-stage production `Dockerfile`** that builds both the Next.js enterprise UI and the FastAPI crawler backend into a **single, unified Render Web Service**.

---

## ⚡ Fastest & Easiest Deployment (Single Web Service)

### Step 1: In your Render Dashboard
1. Go to your existing Web Service: [`Anaya-software-`](https://dashboard.render.com/)
2. Or create a new Web Service by clicking **+ New** -> **Web Service** -> select **`Hunter28-lucky/Anaya-software-`**.

### Step 2: Render Detects `Dockerfile` Automatically
Render will automatically detect the root `Dockerfile`:
- **Language / Runtime:** Docker
- **Region:** Oregon (or closest to you)
- **Instance Type:** Free

### Step 3: Add Environment Variables
In the **Environment Variables** tab on Render:
1. `OPENROUTER_API_KEY`: `<your_openrouter_api_key>` (Paste your OpenRouter API key here)
2. `OPENROUTER_MODEL`: `nvidia/nemotron-3-super-120b-a12b:free`
3. `DATABASE_URL`: `sqlite+aiosqlite:///./leadqualify.db`

### Step 4: Deploy
Click **"Manual Deploy" -> "Deploy latest commit"** (or Render will automatically start the build on git push).

Within 2–3 minutes:
- Next.js compiles the dashboard UI into static production assets.
- FastAPI starts up on Render's dynamic `$PORT`.
- Your app will be live at `https://anaya-software.onrender.com` (or your chosen name)!
- **Zero CORS issues, zero separate service costs, 100% free-tier compatible.**
