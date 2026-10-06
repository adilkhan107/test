import os
from pathlib import Path


def _list(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings:
    def __init__(self) -> None:
        self.data_dir = Path(os.getenv("DATA_DIR", "./data")).resolve()
        self.upload_dir = self.data_dir / "uploads"
        self.snapshot_dir = self.data_dir / "snapshots"

        url = os.getenv("DATABASE_URL", f"sqlite:///{self.data_dir / 'nirmaanai.db'}")
        # Render/Heroku style URLs
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        self.database_url = url

        self.cors_origins = _list(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        )
        self.max_upload_bytes = int(float(os.getenv("MAX_UPLOAD_MB", "200")) * 1024 * 1024)
        self.max_video_seconds = float(os.getenv("MAX_VIDEO_SECONDS", "900"))
        self.sample_every_seconds = float(os.getenv("SAMPLE_EVERY_SECONDS", "1.0"))
        self.required_ppe = set(_list(os.getenv("REQUIRED_PPE", "hardhat,vest,mask")))

        self.conf_threshold = float(os.getenv("CONF_THRESHOLD", "0.25"))
        self.model_repo = os.getenv("MODEL_REPO", "mancalazure/construction-ppe-safety")
        self.model_filename = os.getenv("MODEL_FILENAME", "best.pt")
        self.model_revision = os.getenv("MODEL_REVISION") or None

        self.max_incidents_per_video = 300
        self.max_snapshots = 5
        self.allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

    def ensure_dirs(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
