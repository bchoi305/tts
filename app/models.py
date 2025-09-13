from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class TTSJobRequest(BaseModel):
    preset: str = Field(default="Frank [EN]", description="VibeVoice voice preset")


class TTSJobStatus(BaseModel):
    job_id: str
    status: str
    error: Optional[str] = None
    audio_url: Optional[str] = None
    total_chunks: Optional[int] = None
    processed_chunks: Optional[int] = None


class VoiceList(BaseModel):
    presets: list[str]
