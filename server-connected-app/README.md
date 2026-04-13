# Desktop App (Server Connected)

Thin desktop client that captures screen regions and sends images to a backend API.

## Behavior

- Tray app with global hotkey snipping workflow
- Uploads image to backend endpoint
- Polls backend status endpoint while processing
- Displays returned summary in popup

## Default Backend

The default server URL in `ui/components.py` is:
- `https://realitylens-demo.onrender.com`

If you want local development backend, update `AnalyzerWorker(..., server_url=...)` in `server-connected-app/ui/components.py`.

## Run

From repository root:

```bash
python server-connected-app/main.py
```

Hotkey:
- Windows/Linux: `Ctrl+Shift+L`
- macOS: `Cmd+Shift+L`

## Backend Contract

Expected endpoints on the configured server:
- `POST /ai_client`
- `GET /status`
