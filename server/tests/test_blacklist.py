from app.api.leaderboards import FactionWinRateAPI, MIN_PLAYER_MATCHES, WinRateAPI
from app.api.nemesis import KilledByAPI, KilledByRateAPI
from app.api.state import StatsAPI
from app.core import blacklist
from app.core.api_manager import APIManager
from app.core.models import KillLog, Match, MatchPlayer


def _add_player_rows(
    db,
    player_name: str,
    wins: int = 3,
    matches: int = MIN_PLAYER_MATCHES,
) -> None:
    for index in range(matches):
        match_id = f"{player_name}-{index}"
        db.add(Match(match_id=match_id, game_mode="wathe:murder"))
        db.add(
            MatchPlayer(
                match_id=match_id,
                player_name=player_name,
                faction="CIVILIAN",
                role="wathe:civilian",
                is_winner=index < wins,
                end_status="ALIVE",
            )
        )
    db.commit()


def test_blacklist_reloads_and_filters_queries(db, tmp_path, monkeypatch):
    blacklist_file = tmp_path / "blacklist.txt"
    blacklist_file.write_text("# comment\nHiddenPlayer\n", encoding="utf-8")
    monkeypatch.setattr(blacklist, "BLACKLIST_FILE", blacklist_file)

    _add_player_rows(db, "VisiblePlayer", wins=2)
    _add_player_rows(db, "HiddenPlayer", wins=5)

    assert blacklist.is_blacklisted("hiddenplayer")
    reply = WinRateAPI().execute(db=db)["reply"]
    assert "VisiblePlayer" in reply
    assert "HiddenPlayer" not in reply

    manager = APIManager()
    error = manager._validate_player(StatsAPI(), "HiddenPlayer", db)
    missing_error = manager._validate_player(StatsAPI(), "MissingPlayer", db)
    assert error == "❌ 找不到玩家【HiddenPlayer】的对局记录。"
    assert missing_error == "❌ 找不到玩家【MissingPlayer】的对局记录。"
    assert "屏蔽" not in error

    blacklist_file.write_text("", encoding="utf-8")
    assert not blacklist.is_blacklisted("HiddenPlayer")
    assert "HiddenPlayer" in WinRateAPI().execute(db=db)["reply"]


def test_leaderboard_requires_twenty_matches(db, tmp_path, monkeypatch):
    blacklist_file = tmp_path / "blacklist.txt"
    blacklist_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(blacklist, "BLACKLIST_FILE", blacklist_file)

    _add_player_rows(db, "NineteenMatches", matches=MIN_PLAYER_MATCHES - 1)
    _add_player_rows(db, "TwentyMatches", matches=MIN_PLAYER_MATCHES)

    reply = WinRateAPI().execute(db=db)["reply"]
    assert "NineteenMatches" not in reply
    assert "TwentyMatches" in reply

    faction_reply = FactionWinRateAPI().execute(
        db=db,
        player_name="civilian",
    )["reply"]
    assert "NineteenMatches" not in faction_reply
    assert "TwentyMatches" in faction_reply


def test_blacklist_hides_names_from_nemesis_lists(db, tmp_path, monkeypatch):
    blacklist_file = tmp_path / "blacklist.txt"
    blacklist_file.write_text("HiddenKiller\n", encoding="utf-8")
    monkeypatch.setattr(blacklist, "BLACKLIST_FILE", blacklist_file)

    _add_player_rows(db, "VisibleVictim")
    db.add_all(
        [
            MatchPlayer(
                match_id="VisibleVictim-0",
                player_name="HiddenKiller",
                faction="CIVILIAN",
                role="wathe:civilian",
                is_winner=False,
                end_status="ALIVE",
            ),
            MatchPlayer(
                match_id="VisibleVictim-1",
                player_name="VisibleKiller",
                faction="CIVILIAN",
                role="wathe:civilian",
                is_winner=False,
                end_status="ALIVE",
            ),
            KillLog(
                match_id="VisibleVictim-0",
                killer_name="HiddenKiller",
                victim_name="VisibleVictim",
            ),
            KillLog(
                match_id="VisibleVictim-1",
                killer_name="VisibleKiller",
                victim_name="VisibleVictim",
            ),
        ]
    )
    db.commit()

    reply = KilledByAPI().execute(player_name="VisibleVictim", db=db)["reply"]
    assert "VisibleKiller" in reply
    assert "HiddenKiller" not in reply

    rate_reply = KilledByRateAPI().execute(
        player_name="VisibleVictim",
        db=db,
    )["reply"]
    assert "VisibleKiller" in rate_reply
    assert "HiddenKiller" not in rate_reply
