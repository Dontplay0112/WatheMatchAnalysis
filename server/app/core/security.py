import hmac
import secrets

from fastapi import HTTPException, Request, status

from app.core.paths import API_TOKEN_FILE, ensure_data_directories


def ensure_api_token() -> str:
    """Return the write API token, generating a private one on first start."""
    ensure_data_directories()

    try:
        token = API_TOKEN_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        token = ""

    if token:
        return token

    token = secrets.token_urlsafe(32)
    try:
        with API_TOKEN_FILE.open("x", encoding="utf-8") as token_file:
            token_file.write(token + "\n")
        API_TOKEN_FILE.chmod(0o600)
    except FileExistsError:
        token = API_TOKEN_FILE.read_text(encoding="utf-8").strip()
        if not token:
            raise RuntimeError(f"API token file is empty: {API_TOKEN_FILE}")

    return token


def require_write_token(request: Request) -> None:
    expected = ensure_api_token()
    provided = request.headers.get("X-Wathe-Token") or request.query_params.get("token")
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或无效的 Wathe 写入令牌",
        )
