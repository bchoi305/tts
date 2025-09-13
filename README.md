# Document-to-Speech (VibeVoice)

FastAPI + RQ worker that converts uploaded documents (.pdf, .docx, .txt) to speech using fal.ai VibeVoice, assembling the result and storing locally or on S3/MinIO. Includes a simple React frontend.

## Quick Start

- Python 3.11+
- Redis running locally or via Docker
- ffmpeg installed (or use Docker)

### Local (API + Worker)

1. Copy env: `cp .env.example .env` (MOCK_TTS=true by default)
2. Install deps: `pip install -r requirements.txt`
3. In one terminal: `make dev`
4. In another: `make worker`
5. Frontend (optional):
   - `cd frontend && npm install && npm run dev`
   - Set `VITE_API_URL` to `http://localhost:8000` if serving from a different origin

Open the frontend at the Vite URL (default http://localhost:5173) or call the API directly:
- `POST /tts` (multipart: `file`, `preset`)
- `GET /tts/{job_id}` → `{ status, audio_url }`

Static files (local storage backend) are served at `/files/...` by the API.

### Docker Compose (Full stack)

- `cp .env.example .env`
- `make up` (builds API image, launches Redis + MinIO + API + Worker)
- API at http://localhost:8000, Redis at 6379, MinIO at 9000/9001

To use S3/MinIO storage:
- Set `STORAGE_BACKEND=s3`
- Ensure bucket `STORAGE_BUCKET` exists (create in MinIO console) and access keys/env are set

To use real VibeVoice:
- Set `MOCK_TTS=false`
- Set `FAL_KEY=...`

## Design

- `app/parser.py` — parse .txt/.docx/.pdf to text
- `app/splitter.py` — sentence-aware chunker (~400–700 chars)
- `app/tts.py` — fal.ai VibeVoice client (+ mock mode)
- `app/audio_utils.py` — download/generate segments, concat + loudnorm
- `app/storage.py` — local or S3/MinIO upload + URL
- `app/main.py` — FastAPI endpoints `/tts`, `/tts/{job_id}`
- `app/worker.py` — RQ job `process_tts_job` and enqueue helper

Statuses: `queued`, `started/running`, `finished`, `failed` (RQ built-in). On success, `audio_url` is returned.

## Notes

- In MOCK_TTS mode, the worker generates short tones per chunk to validate flow without network.
- Ensure ffmpeg availability; Dockerfile installs ffmpeg.
- For MinIO, create the bucket and optionally set a public policy or rely on pre-signed URLs.

## License

Internal project scaffold — add a license if needed.

