from fastapi.testclient import TestClient

from app.api import upload
from app.core import blacklist, security
from app.core.database import get_db
from app.main import app


def test_http_gateway_and_protected_upload(db, tmp_path, monkeypatch):
    token_file = tmp_path / "api_token.txt"
    matches_dir = tmp_path / "matches"
    matches_dir.mkdir()
    blacklist_file = tmp_path / "blacklist.txt"
    blacklist_file.write_text("BlockedPlayer\n", encoding="utf-8")

    monkeypatch.setattr(security, "API_TOKEN_FILE", token_file)
    monkeypatch.setattr(upload, "MATCHES_DIR", matches_dir)
    monkeypatch.setattr(blacklist, "BLACKLIST_FILE", blacklist_file)
    token = security.ensure_api_token()

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
        assert "屏蔽" in blocked.json()["reply"]

        assert client.post("/api/upload_match", json=match).status_code == 401
        uploaded = client.post(
            "/api/upload_match",
            json=match,
            headers={"X-Wathe-Token": token},
        )
        assert uploaded.status_code == 200
        assert uploaded.json()["status"] == "success"
        saved_files = list(matches_dir.glob("*.json"))
        assert len(saved_files) == 1
        assert saved_files[0].parent == matches_dir
    finally:
        app.dependency_overrides.clear()
