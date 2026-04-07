from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.base_api import BaseAPICommand
from app.core.database import get_db
from app.core.models import MatchPlayer, DeathLog
from app.core.translator import tr
from app.utils import format_reply

class DeathsAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["deaths", "d"]

    @property
    def description(self) -> str:
        return "☠️ 详细死因分析"

    def execute(self, player_name: str, db: Session = Depends(get_db)):
        # 不再自行检查存在的异常，交给 API manager 统一检查

        deaths = db.query(func.count(DeathLog.id)).filter(DeathLog.victim_name == player_name).scalar() or 0
        death_reasons = db.query(
            DeathLog.death_reason, func.count(DeathLog.id).label("count")
        ).filter(DeathLog.victim_name == player_name).group_by(DeathLog.death_reason).all()

        translated_reasons = {}
        for r in death_reasons:
            t = tr("death_reasons", r.death_reason)
            translated_reasons[t] = translated_reasons.get(t, 0) + r.count

        # 排序
        sorted_reasons = sorted(translated_reasons.items(), key=lambda x: x[1], reverse=True)

        # 🌟 构建最终回复文本
        reply = f"☠️ 【{player_name}】死因分析\n总计阵亡: {deaths} 次\n----------------------\n"
        
        if not sorted_reasons:
            reply += "ta还未尝过死亡的滋味！"
        else:
            for reason, count in sorted_reasons:
                reply += f"死于 [{reason}]: {count} 次\n"
                

        reply = format_reply(reply)  # 添加分割线以优化显示效果
        return {"reply": reply.strip()}