from app.api.nemesis import (
    MIN_SHARED_MATCHES,
    KilledByAPI,
    KilledByRateAPI,
    KillingAPI,
    KillingRateAPI,
)
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


def test_relationship_commands_require_more_than_twenty_shared_matches(db):
    for index in range(MIN_SHARED_MATCHES + 1):
        _add_match(db, f"eligible-{index}", "Alice", "Bob")
    for index in range(MIN_SHARED_MATCHES):
        _add_match(db, f"threshold-{index}", "Alice", "Charlie")
    _add_match(db, "alice-only", "Alice")

    db.add_all(
        [
            KillLog(match_id="eligible-0", killer_name="Alice", victim_name="Bob"),
            KillLog(match_id="eligible-1", killer_name="Alice", victim_name="Bob"),
            # 同一局的重复事件只按一局计算。
            KillLog(match_id="eligible-1", killer_name="Alice", victim_name="Bob"),
            KillLog(match_id="eligible-2", killer_name="Bob", victim_name="Alice"),
            # 共同对局恰好 20 场的 Charlie 必须被四个指令全部过滤。
            KillLog(match_id="threshold-0", killer_name="Alice", victim_name="Charlie"),
            KillLog(match_id="threshold-1", killer_name="Charlie", victim_name="Alice"),
            # 不属于共同对局的数据不会进入概率分子。
            KillLog(match_id="alice-only", killer_name="Alice", victim_name="Bob"),
        ]
    )
    db.commit()

    replies = {
        "k": KillingAPI().execute(player_name="Alice", db=db)["reply"],
        "kb": KilledByAPI().execute(player_name="Alice", db=db)["reply"],
        "kr": KillingRateAPI().execute(player_name="Alice", db=db)["reply"],
        "kbr": KilledByRateAPI().execute(player_name="Alice", db=db)["reply"],
    }

    assert "1. Bob - 3次" in replies["k"]
    assert "1. Bob - 1次" in replies["kb"]
    assert "1. Bob - 9.5% (2/21)" in replies["kr"]
    assert "1. Bob - 4.8% (1/21)" in replies["kbr"]
    assert all("Charlie" not in reply for reply in replies.values())
