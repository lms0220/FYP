# ScamShield browser extension

Chrome/Edge (Manifest V3) extension that checks the current page with the backend's `/predict` endpoint.

## Install (unpacked)

1. Start the backend (`docker compose up`, or `python backend/app.py`) so it listens on `http://localhost:5000`.
2. Open `chrome://extensions`, enable **Developer mode**, click **Load unpacked** and select this `extension/` folder.
3. Click the extension icon on any http(s) page to see the verdict.

Tick **Check every page automatically** to show an `OK` / `!` badge on each tab. This is off by default because it sends every visited URL to the backend.

## Limits

- The backend address is fixed to `localhost:5000` (see `api.js` and `host_permissions` in `manifest.json`).
- Results are cached for 10 minutes. `localhost` pages are never checked.
- The first check can be slow when the local LLM explanation is generated.
