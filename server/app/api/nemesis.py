from fastapi import Depends
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased

from app.core.base_api import BaseAPICommand
from app.core.blacklist import visible_player
from app.core.database import get_db
from app.core.models import KillLog, MatchPlayer
from app.utils import format_reply


def _relationship_rates(
    db: Session,
    player_name: str,
    *,
    killed_by: bool,
) -> list[dict]:
    """Calculate per-opponent rates using distinct shared matches."""
    player_matches = select(MatchPlayer.match_id).where(
        MatchPlayer.player_name == player_name
    ).distinct()
    other_name = KillLog.killer_name if killed_by else KillLog.victim_name
    relation_filter = (
        KillLog.victim_name == player_name
        if killed_by
        else KillLog.killer_name == player_name
    )
    other_presence = aliased(MatchPlayer)

    relation_rows = db.query(
        other_name.label("other_name"),
        func.count(func.distinct(KillLog.match_id)).label("relation_count"),
    ).join(
        other_presence,
        and_(
            other_presence.match_id == KillLog.match_id,
            other_presence.player_name == other_name,
        ),
    ).filter(
        relation_filter,
        other_name != player_name,
        other_name.isnot(None),
        KillLog.match_id.in_(player_matches),
        visible_player(other_name),
    ).group_by(other_name).all()

    other_names = [row.other_name for row in relation_rows if row.other_name]
    if not other_names:
        return []

    shared_rows = db.query(
        MatchPlayer.player_name.label("other_name"),
        func.count(func.distinct(MatchPlayer.match_id)).label("shared_count"),
    ).filter(
        MatchPlayer.player_name.in_(other_names),
        MatchPlayer.match_id.in_(player_matches),
        visible_player(MatchPlayer.player_name),
    ).group_by(MatchPlayer.player_name).all()
    shared_counts = {row.other_name: row.shared_count for row in shared_rows}

    rates = []
    for row in relation_rows:
        shared_count = shared_counts.get(row.other_name, 0)
        if shared_count:
            rates.append(
                {
                    "name": row.other_name,
                    "relation_count": row.relation_count,
                    "shared_count": shared_count,
                    "rate": row.relation_count / shared_count,
                }
            )

    return sorted(
        rates,
        key=lambda row: (-row["rate"], -row["relation_count"], row["name"].casefold()),
    )[:10]


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
            KillLog.killer_name.isnot(None),
            visible_player(KillLog.killer_name),
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
            KillLog.victim_name.isnot(None),
            visible_player(KillLog.victim_name),
        ).group_by(KillLog.victim_name).order_by(func.count(KillLog.id).desc()).limit(10).all()
        
        reply = f"    🎯 【{player_name}】：我在杀谁~\n"
        if not results:
            reply += "你还没有击杀过任何人！\n"
        else:
            for i, r in enumerate(results, 1):
                reply += f"{i}. {r.victim_name} - {r.count}次\n"
                
        reply = format_reply(reply)
        return {"reply": reply.strip()}


class KillingRateAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["kr"]

    @property
    def description(self) -> str:
        return "🎯 我击杀其他玩家的同场概率排行"

    def execute(self, player_name: str, db: Session = Depends(get_db)):
        results = _relationship_rates(db, player_name, killed_by=False)

        reply = f"    🎯 【{player_name}】：我在杀谁~（同场击杀概率）\n"
        if not results:
            reply += "你还没有击杀过任何人！\n"
        else:
            for index, row in enumerate(results, 1):
                reply += (
                    f"{index}. {row['name']} - {row['rate'] * 100:.1f}% "
                    f"({row['relation_count']}/{row['shared_count']})\n"
                )

        return {"reply": format_reply(reply).strip()}


class KilledByRateAPI(BaseAPICommand):
    @property
    def action(self) -> list[str]:
        return ["kbr"]

    @property
    def description(self) -> str:
        return "🔪 我被其他玩家击杀的同场概率排行"

    def execute(self, player_name: str, db: Session = Depends(get_db)):
        results = _relationship_rates(db, player_name, killed_by=True)

        reply = f"🔪 【{player_name}】：谁在杀我？！（同场被击杀概率）\n"
        if not results:
            reply += "你还没有被任何人击杀过！\n"
        else:
            for index, row in enumerate(results, 1):
                reply += (
                    f"{index}. {row['name']} - {row['rate'] * 100:.1f}% "
                    f"({row['relation_count']}/{row['shared_count']})\n"
                )

        return {"reply": format_reply(reply).strip()}
