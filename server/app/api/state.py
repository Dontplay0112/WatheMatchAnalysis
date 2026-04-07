from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer, case

from app.core.base_api import BaseAPICommand
from app.core.database import get_db
from app.core.models import MatchPlayer, DeathLog, KillLog
from app.utils import format_reply

class StatsAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["stats", "st"]

    @property
    def description(self) -> str:
        return "📊 基础对局数据"

    def execute(self, player_name: str, db: Session = Depends(get_db)):
        # 1. 查询基础对局
        base_stats = db.query(
            func.count(MatchPlayer.id).label("total_matches"),
            func.sum(func.cast(MatchPlayer.is_winner, Integer)).label("total_wins"),
            func.sum(case((MatchPlayer.end_status == "ALIVE", 1), else_=0)).label("total_survivals")
        ).filter(MatchPlayer.player_name == player_name).first()

        total_matches = base_stats.total_matches or 0
        if total_matches == 0:
            raise HTTPException(status_code=404, detail="找不到该玩家的对局记录")

        wins = base_stats.total_wins or 0
        survivals = base_stats.total_survivals or 0
        
        # 2. 查询战斗数据 (使用全新的 KillLog 和 DeathLog)
        kills = db.query(func.count(KillLog.id)).filter(KillLog.killer_name == player_name).scalar() or 0
        deaths = db.query(func.count(DeathLog.id)).filter(DeathLog.victim_name == player_name).scalar() or 0
        
        # 计算小脑操作 (TK): 凶手是自己，且受害者阵营与自己相同，且都不是 UNKNOWN, 
        tk_count = 0
        # tk_count = db.query(func.count(KillLog.id)).filter(
        #     KillLog.killer_name == player_name,
        #     KillLog.killer_faction == KillLog.victim_faction,
        #     KillLog.killer_faction != "KILLER",
        #     KillLog.killer_faction != "KILLER",
        #     KillLog.victim_faction != "UNKNOWN"
        # ).scalar() or 0
        tk_count = db.query(func.count(DeathLog.id)).filter(
            DeathLog.victim_name == player_name,
            # DeathLog.victim_faction == "CIVILIAN",
            DeathLog.death_reason == "wathe:shot_innocent",
        ).scalar() or 0

        win_rate = f"{(wins / total_matches * 100):.1f}"
        surv_rate = f"{(survivals / total_matches * 100):.1f}"

        # 3. 🌟 构建最终回复文本
        reply = (
            f"📊 【{player_name}】数据统计\n"
            f"总对局: {total_matches}场 | 获胜: {wins}场\n"
            f"综合胜率: {win_rate}%\n"
            f"存活概率: {surv_rate}%\n"
            f"击杀: {kills}\n"
            f"死亡: {deaths}\n"
            f"K/D: {(kills / deaths if deaths > 0 else kills):.2f}\n"
        )
        if tk_count > 0:
            reply += f"小脑: {tk_count} 次"
        reply = format_reply(reply)  # 添加分割线以优化显示效果
        # 直接将构建好的文本作为 reply 字段返回
        return {"reply": reply.strip()}