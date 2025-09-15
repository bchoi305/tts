from __future__ import annotations

import os
import uuid
import logging
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from redis import Redis
from rq import Queue
from rq.job import Job

from .config import settings
from .models import TTSJobRequest, TTSJobStatus, VoiceList
from .worker import enqueue_tts_job


logger = logging.getLogger("uvicorn")

app = FastAPI(title="Document-to-Speech API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure dirs
os.makedirs(settings.tmp_dir, exist_ok=True)
os.makedirs(settings.storage_dir, exist_ok=True)

# Serve local storage (if using local backend)
if settings.storage_backend == "local":
    app.mount("/files", StaticFiles(directory=settings.storage_dir), name="files")


@app.post("/tts")
async def create_tts_job(
    file: UploadFile = File(...),
    preset: str = Form(default="Frank [EN]")
):
    if not file:
        raise HTTPException(status_code=400, detail="Missing file upload")
    try:
        # Persist uploaded file to tmp
        suffix = os.path.splitext(file.filename or "upload")[1]
        fname = f"upload-{uuid.uuid4().hex}{suffix}"
        dest = os.path.join(settings.tmp_dir, fname)
        with open(dest, "wb") as f:
            f.write(await file.read())

        selected = preset or settings.fallback_preset
        if settings.presets and selected not in settings.presets:
            logger.warning("Unknown preset '%s' requested; using fallback '%s'", selected, settings.fallback_preset)
            selected = settings.fallback_preset
        job = enqueue_tts_job(dest, file.filename or fname, selected)
        return {"job_id": job.id, "status": "queued"}
    except Exception as e:
        logger.exception("Failed to enqueue TTS job: %s", e)
        raise HTTPException(status_code=500, detail="Failed to enqueue job")


@app.get("/tts/{job_id}", response_model=TTSJobStatus)
async def get_tts_status(job_id: str):
    redis = Redis.from_url(settings.redis_url)
    try:
        job = Job.fetch(job_id, connection=redis)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    status = job.get_status(refresh=True)
    audio_url: Optional[str] = None
    error: Optional[str] = None
    total_chunks = None
    processed_chunks = None

    if status == "finished":
        audio_url = job.result
    elif status == "failed":
        error = str(job.exc_info).splitlines()[-1] if job.exc_info else "Unknown error"
    # read progress meta if present
    try:
        meta = job.meta or {}
        total_chunks = meta.get("total_chunks")
        processed_chunks = meta.get("processed_chunks")
    except Exception:
        pass

    return TTSJobStatus(
        job_id=job_id,
        status=status,
        audio_url=audio_url,
        error=error,
        total_chunks=total_chunks,
        processed_chunks=processed_chunks,
    )


@app.get("/")
async def root():
    return {"ok": True, "service": "Document-to-Speech API"}


@app.get("/voices", response_model=VoiceList)
async def list_voices():
    # For now, return configured presets (can extend to pull from fal.ai if API allows listing)
    return VoiceList(presets=settings.presets)
