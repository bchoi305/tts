from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    # API
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    base_url: str | None = os.getenv("BASE_URL")

    # Redis / RQ
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    queue_name: str = os.getenv("QUEUE_NAME", "tts")

    # Storage
    storage_backend: str = os.getenv("STORAGE_BACKEND", "local")  # local | s3
    storage_dir: str = os.getenv("STORAGE_DIR", "storage")

    # S3 / MinIO
    s3_bucket: str | None = os.getenv("STORAGE_BUCKET")
    s3_endpoint_url: str | None = os.getenv("AWS_ENDPOINT_URL")
    s3_region: str | None = os.getenv("AWS_REGION")
    s3_access_key: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    s3_secret_key: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")

    # FAL / VibeVoice
    fal_key: str | None = os.getenv("FAL_KEY")
    fal_url: str = os.getenv("FAL_URL", "https://fal.run/fal-ai/vibevoice")
    mock_tts: bool = os.getenv("MOCK_TTS", "false").lower() in {"1", "true", "yes"}
    presets: list[str] = field(default_factory=lambda: (
        [p.strip() for p in os.getenv("PRESETS", "").split(",") if p.strip()]
        or [
            "Frank [EN]",
            "Emma [EN]",
            "Alice [EN]",
            "Morgan [EN]",
            "James [EN]",
            "Olivia [EN]",
        ]
    ))

    # Runtime
    tmp_dir: str = os.getenv("TMP_DIR", "tmp")
    tts_job_timeout: int = int(os.getenv("TTS_JOB_TIMEOUT", "1800"))  # seconds


settings = Settings()
