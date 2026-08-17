from fastapi import HTTPException
from starlette.requests import Request

from app.api.upload import _safe_match_filename
from app.core import security


def _request(query: bytes = b"", token: str | None = None) -> Request:
    headers = [] if token is None else [(b"x-wathe-token", token.encode("ascii"))]
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/upload_match",
            "headers": headers,
            "query_string": query,
        }
    )


def test_write_token_is_generated_and_required(tmp_path, monkeypatch):
    token_file = tmp_path / "api_token.txt"
    monkeypatch.setattr(security, "API_TOKEN_FILE", token_file)

    token = security.ensure_api_token()
    assert token_file.read_text(encoding="utf-8").strip() == token

    try:
        security.require_write_token(_request())
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("missing token must be rejected")

    security.require_write_token(_request(token=token))
    security.require_write_token(_request(query=f"token={token}".encode("ascii")))


def test_upload_filename_cannot_escape_matches_directory():
    filename = _safe_match_filename(
        {"matchId": "../../outside", "startMs": 1_700_000_000_000}
    )
    assert "/" not in filename
    assert "\\" not in filename
    assert filename.endswith(".json")
