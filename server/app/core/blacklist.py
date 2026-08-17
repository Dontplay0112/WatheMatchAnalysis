from sqlalchemy import func, true

from app.core.paths import BLACKLIST_FILE


def load_blacklist() -> frozenset[str]:
    """Load player names from disk so edits apply without restarting the server."""
    try:
        lines = BLACKLIST_FILE.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return frozenset()

    names = {
        line.strip().casefold()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    }
    return frozenset(names)


def is_blacklisted(player_name: str | None) -> bool:
    if not player_name:
        return False
    return player_name.strip().casefold() in load_blacklist()


def visible_player(column):
    """Return a SQL expression that excludes currently blacklisted names."""
    names = load_blacklist()
    if not names:
        return true()
    return func.lower(column).notin_(names)
