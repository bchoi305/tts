from __future__ import annotations

import os
import uuid
import tempfile
from typing import List

import ffmpeg  # type: ignore
import requests

from .config import settings


def download_audio(url: str, suffix: str = ".mp3") -> str:
    os.makedirs(settings.tmp_dir, exist_ok=True)
    local_path = os.path.join(settings.tmp_dir, f"seg-{uuid.uuid4().hex}{suffix}")
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return local_path


def mock_tone(duration: float = 1.0, frequency: int = 440) -> str:
    os.makedirs(settings.tmp_dir, exist_ok=True)
    out_path = os.path.join(settings.tmp_dir, f"mock-{uuid.uuid4().hex}.mp3")
    # Generate a tone as placeholder audio
    (
        ffmpeg
        .input(f"sine=frequency={frequency}:duration={duration}", f="lavfi")
        .output(out_path, acodec="libmp3lame", ar=44100, ac=2, **{"qscale:a": 2}, loglevel="error")
        .overwrite_output()
        .run()
    )
    return out_path


def concat_and_normalize(inputs: List[str], out_path: str) -> str:
    if not inputs:
        raise ValueError("No input audio segments to concatenate")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    streams = [ffmpeg.input(p) for p in inputs]
    joined = ffmpeg.concat(*streams, v=0, a=1)
    audio = joined.filter("loudnorm")
    (
        ffmpeg
        .output(audio, out_path, acodec="libmp3lame", ar=44100, ac=2, **{"qscale:a": 2}, loglevel="error")
        .overwrite_output()
        .run()
    )
    return out_path
