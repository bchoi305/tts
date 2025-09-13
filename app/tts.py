from __future__ import annotations

import os
import uuid
import time
import random
import logging
import requests
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)


def call_vibevoice(script: str, preset: str = "Frank [EN]") -> str:
    payload = {"script": script, "speakers": [{"preset": preset}]}
    headers = {"Authorization": f"Key {settings.fal_key}"}

    # Exponential backoff with jitter
    max_attempts = 5
    base_sleep = 1.0
    last_exc: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.post(settings.fal_url, json=payload, headers=headers, timeout=600)
            if r.status_code == 422:
                # Surface validation errors clearly (often due to unsupported preset)
                msg = None
                try:
                    jd = r.json()
                    msg = jd.get("error") or jd.get("detail")
                except Exception:
                    msg = r.text
                raise requests.HTTPError(f"422 from VibeVoice (possible unsupported preset '{preset}'): {msg}", response=r)
            r.raise_for_status()
            return r.json()["audio"]["url"]
        except requests.RequestException as e:
            last_exc = e
            if attempt == max_attempts:
                break
            delay = base_sleep * (2 ** (attempt - 1))
            delay += random.uniform(0, 0.5)
            logger.warning("VibeVoice request failed (attempt %d/%d): %s; retrying in %.1fs",
                           attempt, max_attempts, e, delay)
            time.sleep(delay)

    # If we got here, all attempts failed
    assert last_exc is not None
    raise last_exc


def should_mock_tts() -> bool:
    return settings.mock_tts or not settings.fal_key
