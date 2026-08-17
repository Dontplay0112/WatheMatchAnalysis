import pytest

from app.core.translator import tr


@pytest.mark.parametrize(
    ("category", "key", "expected"),
    [
        ("factions", "WITCH", "魔女"),
        ("factions", "sparkwitch:witch", "魔女"),
        ("roles", "noellesroles:party_animal", "派对狂"),
        ("roles", "noellesroles:shadow_jester", "影子小丑"),
        ("roles", "sparkwitch:black_raven", "黑羽鸦"),
        ("roles", "sparkwitch:grand_witch", "大魔女"),
        ("roles", "sparkwitch:wraith", "冤魂"),
        ("roles", "announcement.role.sparkwitch.ninja", "忍者"),
        ("death_reasons", "noellesroles:assassin_misfire", "刺客的误判"),
        ("death_reasons", "noellesroles:shadow_bond", "影誓同尽"),
        ("death_reasons", "sparkwitch:ninja_knife_kill", "被苦无刺杀"),
        ("death_reasons", "sparkwitch:tofana_elixir", "仙液反噬"),
    ],
)
def test_updated_mod_translations(category, key, expected):
    assert tr(category, key) == expected
