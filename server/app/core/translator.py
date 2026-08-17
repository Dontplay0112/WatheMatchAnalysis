import json

from app.core.paths import DATA_DIR


TRANSLATIONS_FILE = DATA_DIR / "translations.json"

_mapping = {"factions": {}, "roles": {}, "death_reasons": {}}

if TRANSLATIONS_FILE.exists():
    with TRANSLATIONS_FILE.open('r', encoding='utf-8') as f:
        _mapping.update(json.load(f))

def tr(category: str, key: str) -> str:
    if not key: return "未知"
    mapped = _mapping.get(category, {}).get(key)
    return mapped if mapped else (key.split(":")[-1] if ":" in key else key)
