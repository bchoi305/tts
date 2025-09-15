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


class UnsupportedPresetError(Exception):
    pass


def call_vibevoice(script: str, preset: str = "Frank [EN]") -> str:
    # Pre-validate against configured presets to avoid obviously bad requests
    if settings.presets and preset not in settings.presets:
        raise UnsupportedPresetError(f"Preset '{preset}' is not in allowed presets list")

    payload = {"script": script, "speakers": [{"preset": preset}]}
    headers = {"Authorization": f"Key {settings.fal_key}"}

    # Exponential backoff with jitter
    max_attempts = settings.fal_max_attempts
    base_sleep = 1.0
    last_exc: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.post(
                settings.fal_url,
                json=payload,
                headers=headers,
                timeout=(settings.fal_connect_timeout, settings.fal_read_timeout),
            )
            if r.status_code in (400, 422):
                # Likely validation/preset issue — raise clearly so caller can decide about fallback
                msg = None
                try:
                    jd = r.json()
                    msg = jd.get("error") or jd.get("detail")
                except Exception:
                    msg = r.text
                err = requests.HTTPError(
                    f"{r.status_code} from VibeVoice (possible unsupported preset '{preset}'): {msg}",
                    response=r,
                )
                raise err
            r.raise_for_status()

            # Parse audio URL robustly
            data = r.json()
            audio_url = None
            if isinstance(data, dict):
                # Prefer single 'audio' then try first of 'audios'
                try:
                    audio_url = data.get("audio", {}).get("url")
                except Exception:
                    audio_url = None
                if not audio_url:
                    try:
                        audios = data.get("audios") or []
                        if audios and isinstance(audios, list) and isinstance(audios[0], dict):
                            audio_url = audios[0].get("url")
                    except Exception:
                        audio_url = None
            if not audio_url:
                raise ValueError("VibeVoice response missing audio URL")

            return audio_url
        except requests.RequestException as e:
            last_exc = e
            if attempt == max_attempts:
                break
            delay = base_sleep * (2 ** (attempt - 1))
            delay += random.uniform(0, 0.5)
            logger.warning(
                "VibeVoice request failed (attempt %d/%d, preset=%s): %s; retrying in %.1fs",
                attempt,
                max_attempts,
                preset,
                e,
                delay,
            )
            time.sleep(delay)
        except ValueError as e:
            # Response shape unexpected — don't keep retrying endlessly
            last_exc = e
            break

    # If we got here, all attempts failed
    assert last_exc is not None
    raise last_exc


def should_mock_tts() -> bool:
    return settings.mock_tts or not settings.fal_key
