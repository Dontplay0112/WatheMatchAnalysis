from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer, case

from app.core.base_api import BaseAPICommand
from app.core.database import get_db
from app.core.models import MatchPlayer, KillLog, DeathLog
from app.utils import format_reply

class WinRateAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["winrate", "wr"]

    @property
    def description(self) -> str:
        return "🏆 胜率榜 (≥5局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        results = db.query(
            MatchPlayer.player_name,
            func.count(MatchPlayer.id).label('plays'),
            func.sum(func.cast(MatchPlayer.is_winner, Integer)).label('wins')
        ).group_by(MatchPlayer.player_name).having(func.count(MatchPlayer.id) >= 5).all()

        sorted_res = sorted(results, key=lambda x: x.wins / x.plays if x.plays else 0, reverse=True)[:10]

        reply = "🏆 胜率排行榜 (≥5场)\n"
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
        return "💀 死亡率榜 (≥5局)"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        results = db.query(
            MatchPlayer.player_name,
            func.count(MatchPlayer.id).label('plays'),
            func.sum(case((MatchPlayer.end_status != "ALIVE", 1), else_=0)).label('deaths')
        ).group_by(MatchPlayer.player_name).having(func.count(MatchPlayer.id) >= 5).all()

        sorted_res = sorted(results, key=lambda x: x.deaths / x.plays if x.plays else 0, reverse=True)[:10]

        reply = "💀 死亡率排行榜 (≥5场)\n"
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
        return "⚔️ K/D榜"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        # 获取每个玩家的击杀数
        kills_q = db.query(
            KillLog.killer_name.label("name"),
            func.count(KillLog.id).label("kills")
        ).group_by(KillLog.killer_name).all()
        
        # 获取每个玩家的死亡数 (从 DeathLog)
        deaths_q = db.query(
            DeathLog.victim_name.label("name"),
            func.count(DeathLog.id).label("deaths")
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
            if not name: continue
            k = s["kills"]
            d = s["deaths"]
            if k < 10 or d < 10:  # 只统计至少10杀10死的玩家，避免数据过于稀疏
                continue
            kd = k / d if d > 0 else k
            kd_list.append({"name": name, "k": k, "d": d, "kd": kd})
            
        sorted_res = sorted(kd_list, key=lambda x: x["kd"], reverse=True)[:10]

        reply = "⚔️ K/D排行榜 (前10)\n"
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
        return "🧠 小脑榜"

    @property
    def requires_player(self) -> bool:
        return False

    def execute(self, db: Session = Depends(get_db)):
        results = db.query(
            DeathLog.victim_name,
            func.count(DeathLog.id).label('count')
        ).filter(
            DeathLog.victim_faction == "CIVILIAN",
            DeathLog.death_reason == "wathe:shot_innocent"
        ).group_by(DeathLog.victim_name).order_by(func.count(DeathLog.id).desc()).limit(10).all()

        reply = "🧠 小脑排行榜\n"
        if not results:
            reply += "无人小脑......暂时的......\n"
        for i, r in enumerate(results, 1):
            reply += f"{i}. {r.victim_name} - {r.count}次\n"
            
        reply = format_reply(reply)
        return {"reply": reply.strip()}
