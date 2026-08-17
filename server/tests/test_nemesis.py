from app.api.nemesis import KilledByRateAPI, KillingRateAPI
from app.core.models import KillLog, Match, MatchPlayer


def _add_match(db, match_id: str, *player_names: str) -> None:
    db.add(Match(match_id=match_id, game_mode="wathe:murder"))
    for player_name in player_names:
        db.add(
            MatchPlayer(
                match_id=match_id,
                player_name=player_name,
                faction="CIVILIAN",
                role="wathe:civilian",
                is_winner=False,
                end_status="DEAD",
            )
        )


def test_relationship_rates_use_distinct_shared_matches(db):
    _add_match(db, "shared-1", "Alice", "Bob", "Charlie")
    _add_match(db, "shared-2", "Alice", "Bob", "Charlie")
    _add_match(db, "shared-3", "Alice", "Bob")
    _add_match(db, "shared-4", "Alice", "Bob")
    _add_match(db, "alice-only", "Alice")

    db.add_all(
        [
            KillLog(match_id="shared-1", killer_name="Alice", victim_name="Bob"),
            KillLog(match_id="shared-2", killer_name="Alice", victim_name="Bob"),
            # 同一局的重复事件只按一局计算。
            KillLog(match_id="shared-2", killer_name="Alice", victim_name="Bob"),
            KillLog(match_id="shared-3", killer_name="Bob", victim_name="Alice"),
            KillLog(match_id="shared-1", killer_name="Alice", victim_name="Charlie"),
            KillLog(match_id="shared-1", killer_name="Charlie", victim_name="Alice"),
            KillLog(match_id="shared-2", killer_name="Charlie", victim_name="Alice"),
            # 不属于共同对局的数据不会进入概率分子。
            KillLog(match_id="alice-only", killer_name="Alice", victim_name="Bob"),
        ]
    )
    db.commit()

    killing_reply = KillingRateAPI().execute(player_name="Alice", db=db)["reply"]
    killed_by_reply = KilledByRateAPI().execute(player_name="Alice", db=db)["reply"]

    assert "1. Bob - 50.0% (2/4)" in killing_reply
    assert "2. Charlie - 50.0% (1/2)" in killing_reply
    assert "1. Charlie - 100.0% (2/2)" in killed_by_reply
    assert "2. Bob - 25.0% (1/4)" in killed_by_reply
