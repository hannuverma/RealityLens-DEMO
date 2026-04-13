# Desktop App (src)

Primary Python desktop client for RealityLens.

## Behavior

- Runs in system tray
- Uses global hotkey to launch snipping overlay
- Captures selected screen region
- Runs local AI analysis pipeline and shows result popup

Hotkey:
- Windows/Linux: `Ctrl+Shift+L`
- macOS: `Cmd+Shift+L`

## Requirements

- Python 3.10+
- GUI dependencies from root `requirements.txt`
- `.env` in repository root with:
  - `GEMINI_API_KEY`

## Run

From repository root:

```bash
python src/main.py
```

## Helper Scripts

- `check.py`: Quick key/model test
- `doctor.py`: Environment/model diagnostics
- `ai_client.py`: Local analysis pipeline
