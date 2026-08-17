from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer, case
from itertools import combinations

from app.core.base_api import BaseAPICommand
from app.core.blacklist import visible_player
from app.core.database import get_db
from app.core.models import MatchPlayer, KillLog, DeathLog, ItemUserLog
from app.utils import format_reply


MIN_PLAYER_MATCHES = 20
MIN_DUO_MATCHES = 5


def eligible_player_names(db: Session) -> set[str]:
    rows = db.query(MatchPlayer.player_name).filter(
        MatchPlayer.player_name.isnot(None),
        visible_player(MatchPlayer.player_name),
    ).group_by(MatchPlayer.player_name).having(
        func.count(MatchPlayer.id) >= MIN_PLAYER_MATCHES
    ).all()
    return {row.player_name for row in rows if row.player_name}


class WinRateAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["winrate", "wr"]

    @property
    def description(self) -> str:
        return f"🏆 胜率榜 (≥{MIN_PLAYER_MATCHES}局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        results = db.query(
            MatchPlayer.player_name,
            func.count(MatchPlayer.id).label('plays'),
            func.sum(func.cast(MatchPlayer.is_winner, Integer)).label('wins')
        ).filter(
            visible_player(MatchPlayer.player_name)
        ).group_by(MatchPlayer.player_name).having(
            func.count(MatchPlayer.id) >= MIN_PLAYER_MATCHES
        ).all()

        sorted_res = sorted(results, key=lambda x: x.wins / x.plays if x.plays else 0, reverse=True)[:10]

        reply = f"🏆 胜率排行榜 (≥{MIN_PLAYER_MATCHES}场)\n"
        if not sorted_res:
            reply += "暂无符合条件的玩家数据。\n"
        for i, r in enumerate(sorted_res, 1):
            rate = r.wins / r.plays * 100
            reply += f"{i}. {r.player_name} - {rate:.1f}% ({r.wins}/{r.plays})\n"
            
        reply = format_reply(reply)
        return {"reply": reply.strip()}

class DeathRateAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["deathrate", "dr"]

    @property
    def description(self) -> str:
        return f"💀 死亡率榜 (≥{MIN_PLAYER_MATCHES}局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        results = db.query(
            MatchPlayer.player_name,
            func.count(MatchPlayer.id).label('plays'),
            func.sum(case((MatchPlayer.end_status != "ALIVE", 1), else_=0)).label('deaths')
        ).filter(
            visible_player(MatchPlayer.player_name)
        ).group_by(MatchPlayer.player_name).having(
            func.count(MatchPlayer.id) >= MIN_PLAYER_MATCHES
        ).all()

        sorted_res = sorted(results, key=lambda x: x.deaths / x.plays if x.plays else 0, reverse=True)[:10]

        reply = f"💀 死亡率排行榜 (≥{MIN_PLAYER_MATCHES}场)\n"
        if not sorted_res:
            reply += "暂无符合条件的玩家数据。\n"
        for i, r in enumerate(sorted_res, 1):
            rate = r.deaths / r.plays * 100
            reply += f"{i}. {r.player_name} - {rate:.1f}% ({r.deaths}/{r.plays})\n"
            
        reply = format_reply(reply)
        return {"reply": reply.strip()}

class KDRatioAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["kd"]

    @property
    def description(self) -> str:
        return f"⚔️ K/D榜 (≥{MIN_PLAYER_MATCHES}局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        eligible_names = eligible_player_names(db)

        # 获取每个玩家的击杀数
        kills_q = db.query(
            KillLog.killer_name.label("name"),
            func.count(KillLog.id).label("kills")
        ).filter(
            visible_player(KillLog.killer_name),
            visible_player(KillLog.victim_name),
        ).group_by(KillLog.killer_name).all()
        
        # 获取每个玩家的死亡数 (从 DeathLog)
        deaths_q = db.query(
            DeathLog.victim_name.label("name"),
            func.count(DeathLog.id).label("deaths")
        ).filter(
            visible_player(DeathLog.victim_name)
        ).group_by(DeathLog.victim_name).all()
        
        stats = {}
        for k in kills_q:
            stats.setdefault(k.name, {"kills": 0, "deaths": 0})
            stats[k.name]["kills"] = k.kills
            
        for d in deaths_q:
            stats.setdefault(d.name, {"kills": 0, "deaths": 0})
            stats[d.name]["deaths"] = d.deaths
            
        kd_list = []
        for name, s in stats.items():
            if not name or name not in eligible_names:
                continue
            k = s["kills"]
            d = s["deaths"]
            if k < 10 or d < 10:  # 只统计至少10杀10死的玩家，避免数据过于稀疏
                continue
            kd = k / d if d > 0 else k
            kd_list.append({"name": name, "k": k, "d": d, "kd": kd})
            
        sorted_res = sorted(kd_list, key=lambda x: x["kd"], reverse=True)[:10]

        reply = f"⚔️ K/D排行榜 (≥{MIN_PLAYER_MATCHES}场，≥10杀10死)\n"
        if not sorted_res:
            reply += "暂无击杀记录。\n"
        for i, r in enumerate(sorted_res, 1):
            reply += f"{i}. {r['name']} - KD: {r['kd']:.2f} ({r['k']}杀/{r['d']}死)\n"
            
        reply = format_reply(reply)
        return {"reply": reply.strip()}

class XiaonaoAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["xiaonao", "xn"]

    @property
    def description(self) -> str:
        return f"🧠 小脑榜 (≥{MIN_PLAYER_MATCHES}局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        xiaonao_rows = db.query(
            DeathLog.victim_name,
            func.count(DeathLog.id).label('xiaonao_count')
        ).filter(
            DeathLog.victim_faction == "CIVILIAN",
            DeathLog.death_reason == "wathe:shot_innocent",
            visible_player(DeathLog.victim_name),
        ).group_by(DeathLog.victim_name).all()

        plays_rows = db.query(
            MatchPlayer.player_name,
            func.count(MatchPlayer.id).label('plays')
        ).filter(
            visible_player(MatchPlayer.player_name)
        ).group_by(MatchPlayer.player_name).having(
            func.count(MatchPlayer.id) >= MIN_PLAYER_MATCHES
        ).all()

        plays_map = {row.player_name: row.plays for row in plays_rows if row.player_name}

        prob_list = []
        for row in xiaonao_rows:
            if not row.victim_name:
                continue
            plays = plays_map.get(row.victim_name, 0)
            if plays <= 0:
                continue
            rate = row.xiaonao_count / plays
            prob_list.append({
                "name": row.victim_name,
                "xiaonao_count": row.xiaonao_count,
                "plays": plays,
                "rate": rate,
            })

        sorted_res = sorted(
            prob_list,
            key=lambda x: (x["rate"], x["xiaonao_count"], x["plays"]),
            reverse=True
        )[:]

        reply = f"🧠 小脑概率排行榜 (≥{MIN_PLAYER_MATCHES}场)\n"
        if not sorted_res:
            reply += "无人小脑......暂时的......\n"
        for i, r in enumerate(sorted_res, 1):
            reply += f"{i}. {r['name']} - {r['rate'] * 100:.1f}% ({r['xiaonao_count']}/{r['plays']})\n"
            
        reply = format_reply(reply)
        return {"reply": reply.strip()}


class RevolverAvgUseAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["revolver", "rv", "revolveravg"]

    @property
    def description(self) -> str:
        return f"🔫 平均每局开枪次数 (≥{MIN_PLAYER_MATCHES}局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        plays_rows = db.query(
            MatchPlayer.player_name,
            func.count(MatchPlayer.id).label("plays")
        ).filter(
            visible_player(MatchPlayer.player_name)
        ).group_by(MatchPlayer.player_name).having(
            func.count(MatchPlayer.id) >= MIN_PLAYER_MATCHES
        ).all()

        revolver_rows = db.query(
            ItemUserLog.player_name,
            func.count(ItemUserLog.id).label("uses")
        ).filter(
            ItemUserLog.item == "wathe:revolver",
            visible_player(ItemUserLog.player_name),
        ).group_by(ItemUserLog.player_name).all()

        uses_map = {row.player_name: row.uses for row in revolver_rows if row.player_name}

        stats = []
        for row in plays_rows:
            if not row.player_name:
                continue
            plays = row.plays or 0
            if plays <= 0:
                continue
            uses = uses_map.get(row.player_name, 0)
            stats.append({
                "name": row.player_name,
                "uses": uses,
                "plays": plays,
                "avg": uses / plays,
            })

        sorted_res = sorted(
            stats,
            key=lambda x: (x["avg"], x["uses"], x["plays"]),
            reverse=True
        )[:10]

        reply = f"🔫 平均每局开枪次数 (≥{MIN_PLAYER_MATCHES}场)\n"
        if not sorted_res:
            reply += "暂无符合条件的玩家数据。\n"
        for i, r in enumerate(sorted_res, 1):
            reply += f"{i}. {r['name']} - {r['avg']:.2f}次/局 ({r['uses']}/{r['plays']})\n"

        reply = format_reply(reply)
        return {"reply": reply.strip()}


class GunHitRateAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["gunhit", "ghr", "gunrate"]

    @property
    def description(self) -> str:
        return "🎯 枪命中率榜 (击杀/开枪, ≥20枪)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        shot_rows = db.query(
            ItemUserLog.player_name,
            func.count(ItemUserLog.id).label("shots")
        ).filter(
            ItemUserLog.item == "wathe:revolver"
        ).group_by(ItemUserLog.player_name).having(func.count(ItemUserLog.id) >= 20).all()

        kill_rows = db.query(
            KillLog.killer_name.label("player_name"),
            func.count(KillLog.id).label("kills")
        ).filter(
            KillLog.death_reason == "wathe:gun_shot"
        ).group_by(KillLog.killer_name).all()

        kills_map = {row.player_name: row.kills for row in kill_rows if row.player_name}

        stats = []
        for row in shot_rows:
            if not row.player_name:
                continue
            shots = row.shots or 0
            if shots <= 0:
                continue
            kills = kills_map.get(row.player_name, 0)
            stats.append({
                "name": row.player_name,
                "kills": kills,
                "shots": shots,
                "rate": kills / shots,
            })

        sorted_res = sorted(
            stats,
            key=lambda x: (x["rate"], x["kills"], x["shots"]),
            reverse=True
        )[:10]

        reply = "🎯 枪命中率排行榜 (≥20枪)\n"
        if not sorted_res:
            reply += "暂无符合条件的玩家数据。\n"
        for i, r in enumerate(sorted_res, 1):
            reply += f"{i}. {r['name']} - {r['rate'] * 100:.1f}% ({r['kills']}/{r['shots']})\n"

        reply = format_reply(reply)
        return {"reply": reply.strip()}


class SurvRateAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["survrate", "sr"]

    @property
    def description(self) -> str:
        return f"🛡️ 耐活榜 (≥{MIN_PLAYER_MATCHES}局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        results = db.query(
            MatchPlayer.player_name,
            func.count(MatchPlayer.id).label('plays'),
            func.sum(case((MatchPlayer.end_status == "ALIVE", 1), else_=0)).label('survivals')
        ).filter(
            visible_player(MatchPlayer.player_name)
        ).group_by(MatchPlayer.player_name).having(
            func.count(MatchPlayer.id) >= MIN_PLAYER_MATCHES
        ).all()

        sorted_res = sorted(results, key=lambda x: x.survivals / x.plays if x.plays else 0, reverse=True)[:10]

        reply = f"🛡️ 耐活榜 (≥{MIN_PLAYER_MATCHES}场)\n"
        if not sorted_res:
            reply += "暂无符合条件的玩家数据。\n"
        for i, r in enumerate(sorted_res, 1):
            rate = r.survivals / r.plays * 100
            reply += f"{i}. {r.player_name} - {rate:.1f}% ({r.survivals}/{r.plays})\n"
            
        reply = format_reply(reply)
        return {"reply": reply.strip()}


class KillerDuoWinRateAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["killerduo", "kdw", "duowr"]

    @property
    def description(self) -> str:
        return f"🤝 杀手搭档胜率榜 (双方各≥{MIN_PLAYER_MATCHES}局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        eligible_names = eligible_player_names(db)
        killer_rows = db.query(
            MatchPlayer.match_id,
            MatchPlayer.player_name,
            MatchPlayer.is_winner
        ).filter(
            MatchPlayer.faction == "KILLER",
            visible_player(MatchPlayer.player_name),
            MatchPlayer.player_name.in_(eligible_names),
        ).all()

        match_killers = {}
        for row in killer_rows:
            if not row.match_id or not row.player_name:
                continue
            match_killers.setdefault(row.match_id, []).append(row)

        duo_stats = {}
        for killers in match_killers.values():
            if len(killers) < 2:
                continue

            players = []
            winner_map = {}
            for k in killers:
                if k.player_name in winner_map:
                    # 去重，避免异常数据导致同局同名重复计数
                    winner_map[k.player_name] = winner_map[k.player_name] or bool(k.is_winner)
                    continue
                players.append(k.player_name)
                winner_map[k.player_name] = bool(k.is_winner)

            if len(players) < 2:
                continue

            for p1, p2 in combinations(sorted(players), 2):
                pair_key = (p1, p2)
                duo_stats.setdefault(pair_key, {"plays": 0, "wins": 0})
                duo_stats[pair_key]["plays"] += 1
                if winner_map.get(p1, False) and winner_map.get(p2, False):
                    duo_stats[pair_key]["wins"] += 1

        qualified = []
        for pair, stat in duo_stats.items():
            plays = stat["plays"]
            wins = stat["wins"]
            if plays < MIN_DUO_MATCHES:
                continue
            rate = wins / plays
            qualified.append({"pair": pair, "plays": plays, "wins": wins, "rate": rate})

        sorted_res = sorted(
            qualified,
            key=lambda x: (x["rate"], x["wins"], x["plays"]),
            reverse=True
        )[:10]

        reply = (
            f"🤝 杀手搭档胜率榜 "
            f"(双方各≥{MIN_PLAYER_MATCHES}场，搭档≥{MIN_DUO_MATCHES}场)\n"
        )
        if not sorted_res:
            reply += "暂无符合条件的搭档数据。\n"
        for i, r in enumerate(sorted_res, 1):
            p1, p2 = r["pair"]
            reply += f"{i}. {p1} & {p2} - {r['rate'] * 100:.1f}% ({r['wins']}/{r['plays']})\n"

        reply = format_reply(reply)
        return {"reply": reply.strip()}


class FactionWinRateAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["factionwr", "fwr"]

    @property
    def description(self) -> str:
        return f"🏳️ 阵营玩家胜率榜 (玩家总对局≥{MIN_PLAYER_MATCHES}局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db), faction: str = "", player_name: str = ""):
        # 兼容当前指令网关只传第二参数的场景：允许把 faction 写在 player_name 位置
        faction_raw = (faction or player_name or "").strip().lower()

        faction_alias = {
            "civilian": "CIVILIAN",
            "good": "CIVILIAN",
            "goodguy": "CIVILIAN",
            "平民": "CIVILIAN",
            "好人": "CIVILIAN",
            "killer": "KILLER",
            "杀手": "KILLER",
            "neutral": "NEUTRAL",
            "中立": "NEUTRAL",
            "c": "CIVILIAN",
            "k": "KILLER",
            "n": "NEUTRAL",
        }

        target_faction = faction_alias.get(faction_raw, "") if faction_raw else ""
        if not faction_raw:
            msg = "❌ 请指定阵营参数: civilian/killer/neutral（或 平民/杀手/中立）"
            return {"reply": format_reply(msg).strip()}

        if faction_raw and not target_faction:
            msg = "❌ 阵营参数无效，可用: civilian/killer/neutral（或 平民/杀手/中立）"
            return {"reply": format_reply(msg).strip()}

        eligible_names = eligible_player_names(db)

        results = db.query(
            MatchPlayer.player_name,
            func.count(MatchPlayer.id).label("plays"),
            func.sum(func.cast(MatchPlayer.is_winner, Integer)).label("wins")
        ).filter(
            MatchPlayer.faction == target_faction,
            MatchPlayer.player_name.isnot(None),
            visible_player(MatchPlayer.player_name),
            MatchPlayer.player_name.in_(eligible_names),
        ).group_by(
            MatchPlayer.player_name
        ).all()

        faction_name_cn = {
            "CIVILIAN": "平民",
            "KILLER": "杀手",
            "NEUTRAL": "中立",
        }

        stats = []
        for r in results:
            plays = r.plays or 0
            wins = r.wins or 0
            if plays <= 0:
                continue
            stats.append({
                "player_name": r.player_name,
                "plays": plays,
                "wins": wins,
                "rate": wins / plays,
            })

        sorted_res = sorted(
            stats,
            key=lambda x: (x["rate"], x["wins"], x["plays"]),
            reverse=True
        )[:10]

        title = (
            f"🏳️ {faction_name_cn.get(target_faction, target_faction)}阵营玩家胜率榜 "
            f"(玩家总对局≥{MIN_PLAYER_MATCHES}场)"
        )
        title += "\n"

        reply = title
        if not sorted_res:
            reply += "暂无符合条件的玩家数据。\n"
        for i, row in enumerate(sorted_res, 1):
            reply += f"{i}. {row['player_name']} - {row['rate'] * 100:.1f}% ({row['wins']}/{row['plays']})\n"

        reply = format_reply(reply)
        return {"reply": reply.strip()}
