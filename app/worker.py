from __future__ import annotations

import os
import uuid
import logging
from typing import List

from redis import Redis
from rq import Queue, get_current_job
import requests

from .config import settings
from .parser import parse_file
from .splitter import split_text
from .tts import call_vibevoice, should_mock_tts
from .audio_utils import download_audio, mock_tone, concat_and_normalize
from .storage import save_and_get_url

logger = logging.getLogger(__name__)


def process_tts_job(file_path: str, filename: str, preset: str = "Frank [EN]") -> str:
    text = parse_file(file_path)
    chunks = split_text(text)

    # Progress meta
    job = get_current_job()
    if job:
        job.meta["total_chunks"] = len(chunks)
        job.meta["processed_chunks"] = 0
        job.save_meta()

    seg_paths: List[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        script = f"Speaker 0: {chunk}"
        if should_mock_tts():
            logger.info("[TTS] Mocking chunk %d/%d", idx, len(chunks))
            seg_paths.append(mock_tone(1.2))
        else:
            logger.info("[TTS] Generating chunk %d/%d via VibeVoice (preset=%s)", idx, len(chunks), preset)
            try:
                url = call_vibevoice(script, preset=preset)
            except requests.HTTPError as e:
                # If preset seems unsupported (422), try fallback to Frank [EN]
                if getattr(e, 'response', None) is not None and e.response is not None and e.response.status_code == 422 and preset != "Frank [EN]":
                    logger.warning("[TTS] Preset '%s' failed with 422. Falling back to 'Frank [EN]' for this chunk.", preset)
                    url = call_vibevoice(script, preset="Frank [EN]")
                else:
                    raise
            seg_paths.append(download_audio(url))

        if job:
            job.meta["processed_chunks"] = idx
            job.save_meta()

    # Concatenate + normalize
    os.makedirs(settings.tmp_dir, exist_ok=True)
    out_basename = f"{os.path.splitext(filename)[0]}-{uuid.uuid4().hex[:8]}.mp3"
    out_path = os.path.join(settings.tmp_dir, out_basename)
    final_path = concat_and_normalize(seg_paths, out_path)

    # Upload to storage
    return save_and_get_url(final_path, out_basename)


def enqueue_tts_job(file_path: str, filename: str, preset: str = "Frank [EN]"):
    redis = Redis.from_url(settings.redis_url)
    q = Queue(settings.queue_name, connection=redis)
    job = q.enqueue(
        process_tts_job,
        file_path,
        filename,
        preset,
        job_timeout=settings.tts_job_timeout,
    )
    return job
