from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from app.core.base_api import BaseAPICommand
from app.core.database import get_db
from app.core.models import MatchPlayer
from app.core.translator import tr
from app.utils import format_reply

class RolesAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["roles", "r"]

    @property
    def description(self) -> str:
        return "🎭 阵营与职业胜率"

    def execute(self, player_name: str, db: Session = Depends(get_db)):
        # 不再自行检查存在的异常，交给 API manager 统一检查

        faction_stats = db.query(
            MatchPlayer.faction, func.count(MatchPlayer.id).label("plays"),
            func.sum(func.cast(MatchPlayer.is_winner, Integer)).label("wins")
        ).filter(MatchPlayer.player_name == player_name).group_by(MatchPlayer.faction).all()
        
        role_stats = db.query(
            MatchPlayer.role, func.count(MatchPlayer.id).label("plays"),
            func.sum(func.cast(MatchPlayer.is_winner, Integer)).label("wins")
        ).filter(MatchPlayer.player_name == player_name).group_by(MatchPlayer.role).all()

        fac_dict, role_dict = {}, {}
        for f in faction_stats:
            t = tr("factions", f.faction)
            fac_dict.setdefault(t, {"plays": 0, "wins": 0})
            fac_dict[t]["plays"] += f.plays
            fac_dict[t]["wins"] += f.wins
            
        for r in role_stats:
            t = tr("roles", r.role)
            role_dict.setdefault(t, {"plays": 0, "wins": 0})
            role_dict[t]["plays"] += r.plays
            role_dict[t]["wins"] += r.wins

        # 🌟 构建最终回复文本
        # reply = f"↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓\n"
        reply = f"🎭 【{player_name}】阵营与职业\n------ 阵营 ------\n"
        for fac, stats in fac_dict.items():
            win_rate = f"{(stats['wins'] / stats['plays'] * 100):.1f}"
            reply += f"[{fac}] {stats['plays']}场 胜率{win_rate}%\n"

        reply += "------ 职业 ------\n"
        sorted_roles = sorted(role_dict.items(), key=lambda x: x[1]['plays'], reverse=True)
        for role, stats in sorted_roles:
            win_rate = f"{(stats['wins'] / stats['plays'] * 100):.1f}"
            reply += f"【{role}】 {stats['plays']}场 | 胜率{win_rate}%\n"
        # reply += "\n↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑"
        
        reply = format_reply(reply)  # 添加分割线以优化显示效果

        return {"reply": reply.strip()}