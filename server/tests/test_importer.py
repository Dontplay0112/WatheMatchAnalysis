import json

import pytest

from app.core.importer import SUCCESS, import_match_json
from app.core.models import Match, MatchPlayer


def _match(match_id: str, events: list[dict]) -> dict:
    return {
        "matchId": match_id,
        "gameMode": "wathe:murder",
        "startMs": 1_700_000_000_000,
        "events": events,
    }


def test_failed_import_rolls_back_and_session_remains_usable(db, tmp_path):
    broken_path = tmp_path / "broken.json"
    broken_path.write_text(
        json.dumps(_match("broken", [{"data": {}}])),
        encoding="utf-8",
    )

    with pytest.raises(KeyError):
        import_match_json(db, str(broken_path))
    assert db.query(Match).count() == 0

    valid_path = tmp_path / "valid.json"
    valid_path.write_text(
        json.dumps(
            _match(
                "valid",
                [
                    {
                        "type": "role_assigned",
                        "data": {
                            "player": {
                                "name": "PlayerOne",
                                "role": "wathe:civilian",
                                "faction": "CIVILIAN",
                            }
                        },
                    },
                    {
                        "type": "player_result",
                        "data": {
                            "player": "PlayerOne",
                            "is_winner": 1,
                            "end_status": "ALIVE",
                        },
                    },
                ],
            )
        ),
        encoding="utf-8",
    )

    assert import_match_json(db, str(valid_path)) == SUCCESS
    assert db.query(Match).count() == 1
    assert db.query(MatchPlayer).count() == 1
