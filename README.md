# RealityLens Demo

RealityLens is a multi-client fact-checking project that analyzes screenshots and returns a structured credibility verdict.

This repository contains:
- Desktop clients (standalone AI and server-connected variants)
- A FastAPI backend service
- A React marketing/demo frontend
- An Android client workspace
- Build scripts for packaging desktop binaries

## Repository Layout

- `src/`: Main desktop Python app (local AI pipeline)
- `Double_model_ai/`: Standalone desktop app with Gemini + Groq + Tavily flow
- `server-connected-app/`: Desktop app that sends captures to hosted backend
- `backend/`: FastAPI service exposing analysis endpoints
- `frontend_reality_lens/`: React + Vite frontend
- `Android_App/`: Android Studio project wrapper (`Android_App/Android`)
- `build_all.py`: PyInstaller build script for desktop binaries

## Quick Start

### 1. Python environment

From repository root:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file in the repository root for local AI-enabled clients and backend:

```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
PARALLEL_API_KEY=optional_parallel_key
```

### 3. Run a desktop client

```bash
python src/main.py
```

Global hotkey:
- Windows/Linux: `Ctrl+Shift+L`
- macOS: `Cmd+Shift+L`

### 4. Run backend

```bash
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run frontend

```bash
cd frontend_reality_lens
npm install
npm run dev
```

## Build Desktop Executables

Use:

```bash
python build_all.py
```

This script builds:
- `RealityLens_Standalone` from `Double_model_ai/main.py`
- `RealityLens_Cloud` from `server-connected-app/main.py`

## Module Documentation

See module-specific READMEs:
- `src/README.md`
- `Double_model_ai/README.md`
- `server-connected-app/README.md`
- `backend/README.md`
- `frontend_reality_lens/README.md`
- `Android_App/README.md`
- `Android_App/Android/README.md`
