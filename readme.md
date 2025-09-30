# AI CV Evaluator (Local, Gemini)

A minimalist FastAPI service that:
- accepts CV + Project report (PDF/DOCX/TXT),
- runs a 2-stage Gemini evaluation with RAG,
- returns CV match rate (%), project score (1..5), feedback, and summary,
- simulates long-running processing via background jobs.

## Why this stack
Python + FastAPI + SQLite = zero infra. Gemini for LLM/embeddings. RAG uses SQLite BLOB vectors + NumPy cosine for tiny corpora.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # put GOOGLE_API_KEY
uvicorn app.main:app --reload
```