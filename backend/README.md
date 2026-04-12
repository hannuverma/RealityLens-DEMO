# Backend (FastAPI)

This service exposes RealityLens analysis APIs used by desktop and mobile clients.

## What It Does

- Accepts screenshot/image uploads
- Runs claim extraction and scoring pipeline
- Returns structured analysis output
- Provides real-time status polling during processing

## Endpoints

- `POST /ai_client`: Upload an image file and get analysis result
- `GET /status`: Get current processing status text
- `GET /health_check`: Basic health endpoint

## Requirements

- Python 3.10+
- API keys in environment or `.env`:
  - `GEMINI_API_KEY`
  - `GROQ_API_KEY`
  - `TAVILY_API_KEY`

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

From `backend/`:

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Notes

- Uploaded files are stored temporarily in `temp_uploads/` and deleted after response.
- The app uses a thread pool for blocking analysis tasks so status polling remains responsive.
