# Claim Verification Engine

Multimodal AI-based autonomous claim verification system using Bayesian inference,
Dempster-Shafer evidence fusion, OSINT techniques, and source-credibility network
analysis to produce an explainable verdict with citations and confidence.

## Features

- **Claim Extraction** — atomic claim decomposition using an LLM
- **Evidence Retrieval** — multi-source (Tavily, Exa) parallel search
- **Bayesian Verification** — real-time probability updates with a 95% confidence interval
- **Dempster-Shafer Fusion** — handles conflicting evidence with belief/plausibility intervals
- **OSINT Integration** — Wayback Machine snapshot checks, EXIF metadata, geolocation verification
- **Source Credibility** — network-enhanced credibility scoring
- **Explainable Verdicts** — SUPPORTED / REFUTED / MIXED / UNVERIFIABLE, with reasoning

## Project Structure

```
claim_verification_engine/
├── backend/                 FastAPI service — extraction, retrieval, verification, verdict
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── models/          Pydantic schemas
│       ├── services/        Claim extractor, evidence retriever, Bayesian verifier,
│       │                    OSINT verifier, source credibility, verdict engine, pipeline
│       └── utils/
├── frontend/                Next.js + Tailwind UI (light, editorial theme)
├── tests/                   Pytest integration tests
├── docker-compose.yml
└── pytest.ini
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- API keys: OpenAI, Tavily, Exa, Google (Places/Geocoding)

## Quick Start (local, no Docker)

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in your API keys
uvicorn app.main:app --reload --port 8000
```

**Frontend** (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## Quick Start (Docker)

```bash
export GROQ_API_KEY=your_key   # free: https://console.groq.com

docker-compose up --build
```

## API

- `POST /verify` — verify a claim. Body: `{"text": "..."}`
- `GET /health` — health check

## Testing

```bash
pip install -r backend/requirements.txt
pytest tests/ -v
```

Tests hit live DuckDuckGo search (no key) and Groq (needs `GROQ_API_KEY` set) to pass meaningfully.

## Architecture

See `backend/app/services/pipeline.py` for the main orchestration logic:

```
Input (Text)
   ↓
Claim Extraction & Decomposition (LLM)
   ↓
Multi-Strategy Evidence Retrieval (Tavily + Exa, parallel)
   ↓
Source Credibility Scoring + Entity-Overlap Scoring
   ↓
Verdict Engine (Bayesian + Dempster-Shafer + Weighted Vote, ensembled)
   ↓
Explainable Output (Verdict + Confidence + Reasoning + Evidence)
```
