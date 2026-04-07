import os
import json
from sqlalchemy.orm import Session

# 注意将这里的相对导入替换为你实际的项目路径
from app.core.models import (
    Match, MatchPlayer, DeathLog, KillLog, 
    ItemUserLog, TaskCompleteLog, ShopPurchaseLog, DoorInteractionLog
)

EXPORT_DIR = "data/matches"
SUCCESS = "success"
ERROR = "error"
EXISTS = "exists"

def import_match_json(db: Session, filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    match_id = data.get("matchId")
    if not match_id or db.query(Match).filter_by(match_id=match_id).first():
        return EXISTS
    
    game_mode = data.get("gameMode", "unknown")
    if game_mode not in ["wathe:murder"]:
        return SUCCESS
    
    # 1. 创建主记录
    match_obj = Match(
        match_id=match_id,
        start_ms=data.get("startMs"),
        game_mode=data.get("gameMode"),
        win_status="UNKNOWN" 
    )
    db.add(match_obj)
    
    events = data.get("events", [])
    
    # 2. 第一遍扫描：建立玩家名与角色/阵营的映射
    player_info = {}
    for ev in events:
        if ev["type"] == "role_assigned":
            p_data = ev.get("data", {}).get("player", {})
            p_name = p_data.get("name")
            if p_name:
                player_info[p_name] = {
                    "role": p_data.get("role", "unknown"),
                    "faction": p_data.get("faction", "UNKNOWN")
                }
        elif ev["type"] == "match_end":
            match_obj.win_status = ev.get("data", {}).get("win_status", "UNKNOWN")

    # 3. 第二遍扫描：记录各种流水明细
    for ev in events:
        ev_type = ev["type"]
        ev_data = ev.get("data", {})
        
        # 结算记录
        if ev_type == "player_result":
            p_name = ev_data.get("player")
            info = player_info.get(p_name, {"role": "unknown", "faction": "UNKNOWN"})
            db.add(MatchPlayer(
                match_id=match_id,
                player_name=p_name,
                role=info["role"],
                faction=info["faction"],
                is_winner=bool(ev_data.get("is_winner", 0)),
                end_status=ev_data.get("end_status", "UNKNOWN")
            ))
            
        # 死亡及击杀记录
        elif ev_type == "death":
            victim = ev_data.get("target")
            killer = ev_data.get("actor")
            death_reason = ev_data.get("death_reason", "unknown")
            v_faction = player_info.get(victim, {}).get("faction", "UNKNOWN") if victim else "UNKNOWN"
            
            # 记录受害者视角的 DeathLog
            db.add(DeathLog(
                match_id=match_id,
                victim_name=victim,
                victim_faction=v_faction,
                death_reason=death_reason
            ))
            
            # 如果存在明确的击杀者 (非环境击杀)，单独存入 KillLog
            if killer:
                k_faction = player_info.get(killer, {}).get("faction", "UNKNOWN")
                db.add(KillLog(
                    match_id=match_id,
                    killer_name=killer,
                    killer_faction=k_faction,
                    victim_name=victim,
                    victim_faction=v_faction,
                    death_reason=death_reason
                ))
                
        # 物品使用记录
        elif ev_type == "item_use":
            pos = ev_data.get("pos", {}) # 部分 item_use 可能没有坐标
            db.add(ItemUserLog(
                match_id=match_id,
                player_name=ev_data.get("actor"),
                item=ev_data.get("item"),
                target=ev_data.get("target"),
                pos_x=pos.get("x"),
                pos_y=pos.get("y"),
                pos_z=pos.get("z")
            ))
            
        # 任务完成记录
        elif ev_type == "task_complete":
            p_name = ev_data.get("actor")
            faction = player_info.get(p_name, {}).get("faction", "UNKNOWN")
            
            db.add(TaskCompleteLog(
                match_id=match_id,
                player_name=p_name,
                task_name=ev_data.get("task"),
                # 判断真假任务：只有乘客阵营 CIVILIAN 做的任务才是真任务
                is_real_task=(faction == "CIVILIAN")
            ))
            
        # 商店购买记录
        elif ev_type == "shop_purchase":
            db.add(ShopPurchaseLog(
                match_id=match_id,
                player_name=ev_data.get("actor"),
                item=ev_data.get("item"),
                price_paid=ev_data.get("price_paid", 0),
                balance_after=ev_data.get("balance_after", 0)
            ))
            
        # 门交互记录 (娱乐)
        elif ev_type == "door_interaction":
            db.add(DoorInteractionLog(
                match_id=match_id,
                player_name=ev_data.get("actor"),
                door_type=ev_data.get("door_type"),
                interaction_type=ev_data.get("interaction_type"),
                success=bool(ev_data.get("success", 0))
            ))
            
    db.commit()
    return SUCCESS

def scan_and_import_all(db: Session):
    """扫描文件夹，导入所有新数据"""
    os.makedirs(EXPORT_DIR, exist_ok=True)

    total_count = imported_count = error_count = existing_count = 0
    
    for filename in os.listdir(EXPORT_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(EXPORT_DIR, filename)
            total_count += 1
            try:
                result = import_match_json(db, filepath)
                if result == SUCCESS:
                    imported_count += 1
                elif result == ERROR:
                    error_count += 1
                elif result == EXISTS:
                    existing_count += 1
            except Exception as e:
                print(f"导入 {filename} 时发生错误: {e}")
                error_count += 1

    print(f"扫描完成: 共 {total_count} 个文件, 成功导入 {imported_count} 个, 错误 {error_count} 个, 已存在 {existing_count} 个")