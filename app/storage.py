from __future__ import annotations

import os
import uuid
from typing import Optional

import boto3
from botocore.client import Config as BotoConfig

from .config import settings


def save_local(src_path: str, filename: Optional[str] = None) -> str:
    os.makedirs(settings.storage_dir, exist_ok=True)
    base = filename or os.path.basename(src_path)
    safe_name = base.replace(" ", "_")
    dst = os.path.join(settings.storage_dir, safe_name)
    i = 1
    root, ext = os.path.splitext(dst)
    while os.path.exists(dst):
        dst = f"{root}_{i}{ext}"
        i += 1
    with open(src_path, "rb") as rf, open(dst, "wb") as wf:
        wf.write(rf.read())
    # The API will serve /files as static
    return f"/files/{os.path.basename(dst)}"


def save_s3(src_path: str, filename: Optional[str] = None) -> str:
    if not settings.s3_bucket:
        raise RuntimeError("STORAGE_BUCKET not configured for S3 backend")
    key = filename or os.path.basename(src_path)
    key = key.replace(" ", "_")

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region or "us-east-1",
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=BotoConfig(signature_version="s3v4"),
    )
    with open(src_path, "rb") as f:
        s3.upload_fileobj(f, settings.s3_bucket, key, ExtraArgs={"ContentType": "audio/mpeg"})

    # Generate a pre-signed URL
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=7 * 24 * 3600,
    )
    return url


def save_and_get_url(src_path: str, filename: Optional[str] = None) -> str:
    if settings.storage_backend == "s3":
        return save_s3(src_path, filename)
    return save_local(src_path, filename)

