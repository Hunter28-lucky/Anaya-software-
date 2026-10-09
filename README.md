# LeadQualify AI

**AI Website Qualification & Lead Filtering Platform**

LeadQualify AI is an enterprise-grade web application built to import company website URLs from Excel/CSV workbooks, independently crawl accessible pages using an in-house SSRF-safe crawler, clean and compress first-party business evidence, analyze company operations using the OpenRouter API, cross-verify results against prior research (e.g. Snov.io), and deliver an evidence-backed qualification database with manual review overrides and formula-safe exports.

---

## 🌟 Core Principle

> **A keyword match is not proof of business relevance.**
> A company is **not** classified as a medical tourism provider merely because one page contains the words "medical tourism."

LeadQualify AI strictly differentiates between:
1. **Core Providers:** Companies that genuinely provide or facilitate the target service.
2. **Secondary Businesses:** Companies for which the target service is an auxiliary or partner offering.
3. **Incidental Mentions:** Websites that merely mention the topic in a blog post, news summary, or educational glossary.
4. **Unverifiable Websites:** Sites that are inaccessible, timed out, or blocked (which are **never** auto-rejected without evidence).

---

## 🏛️ System Architecture

```text
LeadQualify AI Architecture
├── Frontend: Next.js 16 (Turbopack, TypeScript, Tailwind CSS, Lucide Icons)
├── Backend: FastAPI (Python 3.10+, Pydantic v2, SQLAlchemy Async, AsyncIO tasks)
├── Custom Crawler: HTTPX + BeautifulSoup + SSRF Resolver + Robots Validator
├── Content Cleaner: Boilerplate/Noise Stripper + Token-Budgeted Business Dossier Builder
├── AI Qualification: OpenRouter API (Claude 3.5 Sonnet / Gemini 2.0 / Llama 3.3)
├── Deterministic Engine: Citation Validator + Editorial Guard + Threshold Enforcer
├── Snov Verifier: Agreement/Contradiction Cross-Checker
├── Database: Supabase PostgreSQL / Local Async SQLite (Multi-tenant isolated with RLS)
└── Security: SSRF DNS Guard + CWE-1236 Formula Injection Sanitizer
```

## ☁️ 1-Click Render Cloud Deployment

Deploy both the backend and frontend to Render in under 2 minutes using the bundled Blueprint:
1. Fork or push this repository to GitHub: `https://github.com/Hunter28-lucky/Anaya-software-`
2. Open [Render Dashboard](https://dashboard.render.com/) -> **New +** -> **Blueprint**.
3. Select your repo and paste your OpenRouter key (`OPENROUTER_API_KEY`).
4. Click **Apply**! Render will automatically deploy both services.
👉 Detailed instructions: [RENDER_DEPLOYMENT.md](file:///Users/krishyogi/Desktop/Anaya%20software%20/RENDER_DEPLOYMENT.md)

---

## 🚀 Local Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- OpenRouter API key (free NVIDIA Nemotron 120B model supported)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (optional for local SQLite testing)
cp ../.env.example .env

# Run FastAPI backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be live at:
- **API Base:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/api/health`

### 2. Frontend Setup

In a new terminal:

```bash
cd frontend

# Install packages
npm install

# Run Next.js development server
npm run dev
```

The frontend dashboard will be live at:
- **Web App:** `http://localhost:3000`

---

## 🧪 Running Automated Tests

Run the full pytest suite (covering SSRF safety, crawler normalization, content cleaning, qualification decision rules, Snov cross-verification, formula injection sanitization, and API routes):

```bash
cd /path/to/project
PYTHONPATH=backend ./backend/.venv/bin/pytest backend/tests -v
```

All 25 automated tests pass with 100% success.

---

## 📂 Sample Datasets Included

Ready-to-use sample lead files are provided in `sample_data/`:
- `sample_data/medical_tourism_leads_sample.csv`
- `sample_data/medical_tourism_leads_sample.xlsx`

These files include realistic test cases:
1. **Genuine Facilitators:** E.g., PlacidWay (classified as `MATCH`).
2. **General Travel Agencies:** E.g., Wanderlust Travel (disqualified as `NOT_A_MATCH`).
3. **Editorial / Blog Mentions:** E.g., Healthcare Trends Digest (flagged as `INCIDENTAL` -> `NOT_A_MATCH` to eliminate false positives).
4. **Hospitals with International Desks:** E.g., Bumrungrad International (evaluated against criteria).
5. **Inaccessible Domains:** Inactive websites safely marked as `UNVERIFIABLE`.

---

## 🛡️ Security Features

### 1. SSRF Protection & Safe DNS Resolution (`backend/app/core/ssrf.py`)
- Restricts schemes strictly to `http` and `https`.
- Resolves target hostnames via `socket.getaddrinfo` before connection.
- Rejects loopback (`127.0.0.0/8`, `::1`), private LANs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local IPs, and cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`).
- Validates every redirect hop independently.

### 2. Anti-Formula Injection (CWE-1236) (`backend/app/core/security.py`)
- Automatically sanitizes exported spreadsheet cells.
- Any cell value starting with `=`, `+`, `-`, `@`, `\t`, `\r`, or `|` is prepended with a single quote `'` to prevent malicious formula execution in Excel or Google Sheets.

### 3. Prompt-Injection Resistance (`backend/app/services/openrouter_service.py`)
- Crawled HTML content is treated as untrusted data and isolated within `<<<UNTRUSTED_WEBSITE_EVIDENCE>>>` delimiter boundaries.
- Explicit system instructions forbid the model from executing any commands found within crawled pages.

### 4. Citation Anti-Hallucination Guard (`backend/app/services/qualification_engine.py`)
- Every cited URL in AI supporting/contradictory evidence is checked against the database of actual fetched crawl pages.
- If an LLM hallucinates an unvisited URL, the result is flagged for human review (`NEEDS_REVIEW`).

---

## 🗄️ Database Migrations & Supabase Deployment

For production deployments on Supabase:
1. Open your Supabase project dashboard.
2. Navigate to the SQL Editor.
3. Run the complete schema script in:
   ```text
   backend/migrations/supabase_schema.sql
   ```
4. Set `DATABASE_URL` in your `.env` to your Supabase PostgreSQL connection string:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

---

## 🐳 Docker Compose Deployment

Run the complete stack with Docker:

```bash
docker compose up --build
```

- **Frontend:** `http://localhost:3000`
- **Backend:** `http://localhost:8000`

---

## 📋 Configurable Industries

While configured for **Medical Tourism** out of the box, LeadQualify AI is industry-agnostic. You can create projects for:
- B2B SaaS Platforms
- IT Staff Augmentation & Outsourcing
- Clean Energy / Solar EPC Contractors
- Specialized Legal & IP Services

Simply define the industry rules in the **Projects & Rules** tab without writing a single line of new code.
