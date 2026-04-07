from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.base_api import BaseAPICommand
from app.core.database import get_db
from app.core.models import KillLog
from app.utils import format_reply

class KilledByAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["killedby", "kb"]

    @property
    def description(self) -> str:
        return "🔪 谁在杀我？！"

    def execute(self, player_name: str, db: Session = Depends(get_db)):
        results = db.query(
            KillLog.killer_name,
            func.count(KillLog.id).label('count')
        ).filter(
            KillLog.victim_name == player_name,
            KillLog.killer_name != player_name, # 排除自杀
            KillLog.killer_name.isnot(None)
        ).group_by(KillLog.killer_name).order_by(func.count(KillLog.id).desc()).limit(10).all()

        reply = f"🔪 【{player_name}】：谁在杀我？！\n"
        if not results:
            reply += "你还没有被任何人击杀过！\n"
        else:
            for i, r in enumerate(results, 1):
                reply += f"{i}. {r.killer_name} - {r.count}次\n"
                
        reply = format_reply(reply)
        return {"reply": reply.strip()}

class KillingAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["killing", "k"]

    @property
    def description(self) -> str:
        return "🎯 我在杀谁~"

    def execute(self, player_name: str, db: Session = Depends(get_db)):
        results = db.query(
            KillLog.victim_name,
            func.count(KillLog.id).label('count')
        ).filter(
            KillLog.killer_name == player_name,
            KillLog.victim_name != player_name, # 排除自杀
            KillLog.victim_name.isnot(None)
        ).group_by(KillLog.victim_name).order_by(func.count(KillLog.id).desc()).limit(10).all()
        
        # 统计总的，两个人在一局的次数,应该是一个列表，对应results中的人,然后计算击杀概率，再修改下面的内容

        reply = f"    🎯 【{player_name}】：我在杀谁~\n"
        if not results:
            reply += "你还没有击杀过任何人！\n"
        else:
            for i, r in enumerate(results, 1):
                reply += f"{i}. {r.victim_name} - {r.count}次\n"
                
        reply = format_reply(reply)
        return {"reply": reply.strip()}
