# Desktop App (Double Model AI)

Standalone RealityLens desktop client with multi-model fallback and search grounding.

## Pipeline Highlights

- Gemini for extraction/scoring primary path
- Groq fallback models for extraction/scoring
- Tavily search grounding
- Optional Parallel search API support

## Requirements

- Python 3.10+
- Dependencies from repository root `requirements.txt`
- `.env` in repository root with:
  - `GEMINI_API_KEY`
  - `GROQ_API_KEY`
  - `TAVILY_API_KEY`
  - `PARALLEL_API_KEY` (optional)

## Run

From repository root:

```bash
python Double_model_ai/main.py
```

Global hotkey:
- Windows/Linux: `Ctrl+Shift+L`
- macOS: `Cmd+Shift+L`

## Diagnostics

- `doctor.py` lists available Groq models for your key.
