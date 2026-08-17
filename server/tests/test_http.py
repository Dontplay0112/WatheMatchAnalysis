from fastapi.testclient import TestClient

from app.api import refresh, upload
from app.core import blacklist
from app.core.database import get_db
from app.main import app


def test_http_gateway_and_open_upload(db, tmp_path, monkeypatch):
    matches_dir = tmp_path / "matches"
    matches_dir.mkdir()
    blacklist_file = tmp_path / "blacklist.txt"
    blacklist_file.write_text("BlockedPlayer\n", encoding="utf-8")

    monkeypatch.setattr(upload, "MATCHES_DIR", matches_dir)
    monkeypatch.setattr(refresh, "scan_and_import_all", lambda db: None)
    monkeypatch.setattr(blacklist, "BLACKLIST_FILE", blacklist_file)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    match = {
        "matchId": "../../safe-after-sanitizing",
        "gameMode": "wathe:murder",
        "startMs": 1_700_000_000_000,
        "events": [],
    }

    try:
        assert client.post("/api", json={"action": "help"}).status_code == 200
        assert client.post("/api", content=b"not-json").status_code == 422
        blocked = client.post(
            "/api",
            json={"action": "stats", "player_name": "blockedplayer"},
        )
        assert blocked.status_code == 200
        assert blocked.json()["reply"] == "❌ 找不到玩家【blockedplayer】的对局记录。"

        assert client.get("/api/refresh").status_code == 200
        uploaded = client.post("/api/upload_match", json=match)
        assert uploaded.status_code == 200
        assert uploaded.json()["status"] == "success"
        saved_files = list(matches_dir.glob("*.json"))
        assert len(saved_files) == 1
        assert saved_files[0].parent == matches_dir
    finally:
        app.dependency_overrides.clear()
