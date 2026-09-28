import os
import uuid
from pathlib import Path
from fastapi import UploadFile

LOCAL_UPLOAD_DIR = Path(os.getenv("LOCAL_UPLOAD_DIR", "uploads"))
LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def save_upload(upload: UploadFile):
    original = Path(upload.filename or "").name
    if not original.strip():
        raise ValueError("Файлдың аты бос болмауы керек.")

    suffix = Path(original).suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    target = LOCAL_UPLOAD_DIR / stored_name

    size = 0
    with target.open("wb") as out:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            size += len(chunk)

    return {
        "original_name": original,
        "stored_name": stored_name,
        "size": size,
        "extension": suffix.lstrip(".") or "file",
        "mime_type": upload.content_type or "application/octet-stream",
        "storage_path": str(target),
    }

def delete_local(stored_name: str):
    target = LOCAL_UPLOAD_DIR / Path(stored_name).name
    if target.exists():
        target.unlink()
