# simpleclock

An app that lets you see the time difference between different time zones not only for the current moment, but also by shifting your local time ±24h.

## Project structure
```
project/
  backend/
    main.py
    requirements.txt
  frontend/
    index.html
    script.js
    style.css
```

## Backend (FastAPI)
1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Start the API server:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

### API endpoints
- `GET /api/timezones?query=<filter>` — returns a list of IANA timezones (optionally filtered by substring).
- `POST /api/time/local` — body: `{ "timezone": "Europe/Paris", "offset_hours": 2 }` returns the shifted current time for the given timezone.
- `POST /api/time/convert` — body: `{ "from_timezone": "Europe/Paris", "to_timezone": "America/New_York", "offset_hours": -3 }` converts the shifted local time into the target timezone.
- `GET /api/health` — simple health check.

## Frontend
The frontend lives in `frontend/` and calls the backend at `http://localhost:8000`.

Serve the files with any static server (for example from the repo root):
```bash
python -m http.server 5500 -d frontend
```
Then open `http://localhost:5500` in your browser while the backend is running.

### Features
- Automatically detects your timezone via the browser; optionally override it using the manual input.
- Searchable list of timezones for selecting a target timezone.
- Slider from –24h to +24h that shifts both clocks in real time.
- Reset button to return to the current time, clear selections, and re-enable auto detection.

## Notes
- The frontend updates the displayed times every second to keep both clocks live.
- Ensure the backend and frontend run from the same machine or adjust `apiBase` in `frontend/script.js` accordingly.
