**Project: Document-to-Speech App (English, using VibeVoice TTS)**

This file defines **agent roles and responsibilities** for building the app.
Agents should follow these instructions when generating or modifying code.

## 1. Agents

### Architect Agent
* Define overall project structure.
* Ensure modular design (parsing, chunking, TTS, audio assembly, API).
* Pick minimal but reliable dependencies.

### Backend Agent
* Implements FastAPI endpoints:
   * POST /tts: Upload document + voice options → enqueue job.
   * GET /tts/{job_id}: Poll job status + return audio URL.
* Implements worker job for:
   * Parsing documents (.pdf, .docx, .txt).
   * Splitting text into manageable chunks (≈400–700 chars).
   * Building TTS script (Speaker 0: ...).
   * Calling **fal.ai VibeVoice** API.
   * Concatenating audio files + normalizing.
   * Uploading final audio to storage (local or S3-compatible).
* Provide logging and error handling.

### Frontend Agent
* Simple web UI (React/Next.js) with:
   * File upload widget.
   * Voice selector (predefined presets).
   * "Generate Audio" button.
   * Job status polling + audio player.
   * Download link.

### DevOps Agent
* Add Dockerfile for backend.
* Provide docker-compose.yml with:
   * API service.
   * Worker service.
   * Redis queue.
   * MinIO (S3-compatible) for storage.
* Add .env.example with required secrets:
   * FAL_KEY=...
   * STORAGE_BUCKET=...
## 2. Backend Instructions

### Dependencies
* fastapi
* uvicorn[standard]
* redis
* rq
* python-docx
* pypdf
* langchain-text-splitters (optional)
* requests
* ffmpeg-python
* boto3 (for S3/MinIO)

### Example: Calling VibeVoice via fal.ai

```python
import requests, os

FAL_URL = "https://fal.run/fal-ai/vibevoice"
FAL_KEY = os.getenv("FAL_KEY")

def call_vibevoice(script: str, preset: str = "Frank [EN]") -> str:
    payload = {
        "script": script,
        "speakers": [{"preset": preset}]
    }
    headers = {"Authorization": f"Key {FAL_KEY}"}
    r = requests.post(FAL_URL, json=payload, headers=headers, timeout=600)
    r.raise_for_status()
    return r.json()["audio"]["url"]
```

## 3. Worker Job Flow
1. Parse input document → plain text.
2. Split into chunks (target ~400–700 chars).
3. For each chunk:
   * Generate script: Speaker 0: <chunk text>.
   * Call call_vibevoice.
   * Download audio segment.
4. Concatenate all audio segments → normalize → save MP3.
5. Upload MP3 to S3/MinIO → return pre-signed URL.
6. Update job status in Redis.
## 4. Frontend Instructions
* Implement a **single-page React app**.
* Use a REST client (fetch or axios) to call FastAPI endpoints.
* On upload:
   * POST file → get job_id.
   * Poll /tts/{job_id} until status = done.
* Show audio player + download button when ready.

## 5. DevOps Setup
* Use docker-compose up to spin up stack.
* Services:
   * api: FastAPI (port 8000).
   * worker: RQ worker (same codebase).
   * redis: Queue broker.
   * minio: S3-compatible storage.
* Add Makefile with tasks:
   * make dev → run API locally.
   * make worker → run worker locally.
   * make up → full stack with Docker.

## 6. Coding Guidelines
* Keep functions short and testable.
* Use type hints (mypy compatible).
* Return JSON with clear status (queued, running, done, error).
* Always log errors with context (doc name, job id).
* Write modular code: parser.py, splitter.py, tts.py, audio_utils.py.

## 7. Stretch Goals (Optional)
* Add chapter markers based on headings.
* Add support for plain text URLs.
* Stream audio chunks progressively instead of waiting for the full file.
* Add multiple preset voices.

