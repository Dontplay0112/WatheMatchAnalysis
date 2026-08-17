from pathlib import Path


SERVER_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = SERVER_DIR / "data"
MATCHES_DIR = DATA_DIR / "matches"
BLACKLIST_FILE = DATA_DIR / "blacklist.txt"
API_TOKEN_FILE = DATA_DIR / "api_token.txt"


def ensure_data_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MATCHES_DIR.mkdir(parents=True, exist_ok=True)
