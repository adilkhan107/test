import os
import tempfile
import time

os.environ["DATA_DIR"] = tempfile.mkdtemp()

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services import video_analyzer  # noqa: E402


class _T:  # tiny stand-in for a torch tensor
    def __init__(self, v):
        self.v = v

    def __getitem__(self, i):
        return self.v


class _Box:
    def __init__(self, c):
        self.cls = _T(c)


class _Result:
    names = {0: "Person", 1: "Hardhat", 2: "NO-Hardhat", 3: "NO-Safety Vest"}

    def __init__(self):
        # 2 people, one without hardhat, one without vest
        self.boxes = [_Box(0), _Box(0), _Box(2), _Box(3)]

    def plot(self):
        return np.zeros((48, 64, 3), dtype=np.uint8)


class _FakeModel:
    def predict(self, frame, **kw):
        return [_Result()]


@pytest.fixture(autouse=True)
def fake_model(monkeypatch):
    monkeypatch.setattr(video_analyzer, "get_model", lambda: _FakeModel())


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def make_video(path, seconds=3, fps=10):
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (64, 48))
    for _ in range(seconds * fps):
        w.write(np.zeros((48, 64, 3), dtype=np.uint8))
    w.release()


def test_full_flow(client, tmp_path):
    vid = tmp_path / "site.mp4"
    make_video(vid)
    r = client.post("/api/vision/analyze", files={"video": ("../../evil name.mp4", vid.read_bytes(), "video/mp4")})
    assert r.status_code == 202
    aid = r.json()["id"]

    for _ in range(50):
        d = client.get(f"/api/vision/analyses/{aid}").json()
        if d["status"] in ("completed", "failed"):
            break
        time.sleep(0.2)
    assert d["status"] == "completed", d
    # 3 sampled frames x 2 people x 3 required checks = 18 checks, 2 violations each -> 6
    assert d["ppe_compliance"] == pytest.approx(100 * (1 - 6 / 18), abs=0.01)
    assert d["peak_people"] == 2
    assert len(d["incidents"]) == 6 and len(d["snapshots"]) == 3
    assert client.get(d["snapshots"][0]["url"]).status_code == 200

    assert not list(video_analyzer.settings.upload_dir.iterdir())  # raw upload removed
    assert client.get(f"/api/risk/{aid}").json()["risk_level"] in ("medium", "high", "critical")
    s = client.get("/api/dashboard/summary").json()
    assert s["completed"] >= 1 and s["total_incidents"] >= 6
    assert client.get("/api/incidents", params={"type": "no_mask"}).json() == []
    assert client.delete(f"/api/vision/analyses/{aid}").status_code == 204
    assert client.get(f"/api/vision/analyses/{aid}").status_code == 404


def test_rejects_bad_files(client):
    assert client.post("/api/vision/analyze", files={"video": ("x.exe", b"abc", "application/octet-stream")}).status_code == 400
    assert client.post("/api/vision/analyze", files={"video": ("x.mp4", b"not a video", "video/mp4")}).status_code == 400
    assert client.post("/api/vision/analyze", files={"video": ("x.mp4", b"", "video/mp4")}).status_code == 400
