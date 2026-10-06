import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings

CHUNK = 1024 * 1024


async def save_upload(file: UploadFile) -> Path:
    """Stream an upload to disk under a random name, enforcing type and size limits."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.allowed_extensions:
        allowed = ", ".join(sorted(settings.allowed_extensions))
        raise HTTPException(400, f"Unsupported file type. Upload one of: {allowed}")

    settings.ensure_dirs()
    dest = settings.upload_dir / f"{uuid.uuid4().hex}{ext}"  # never use the client's filename on disk
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(CHUNK):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(
                        413, f"File is larger than the {settings.max_upload_bytes // (1024 * 1024)} MB limit."
                    )
                out.write(chunk)
    except BaseException:
        dest.unlink(missing_ok=True)
        raise
    if size == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, "The uploaded file is empty.")
    return dest


def save_snapshot(analysis_id: int, rank: int, image: bytes) -> str:
    settings.ensure_dirs()
    name = f"{analysis_id}_{rank}_{uuid.uuid4().hex[:8]}.jpg"
    (settings.snapshot_dir / name).write_bytes(image)
    return name


def delete_snapshots(names: list[str]) -> None:
    for n in names:
        (settings.snapshot_dir / Path(n).name).unlink(missing_ok=True)
