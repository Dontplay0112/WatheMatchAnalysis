from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Match(Base):
    """对局元数据表"""
    __tablename__ = "matches"
    
    match_id = Column(String, primary_key=True)
    start_ms = Column(Integer)
    game_mode = Column(String)
    win_status = Column(String) # 例如: KILLERS, PASSENGERS, NEUTRAL
    
    # 级联关系
    players = relationship("MatchPlayer", back_populates="match", cascade="all, delete")
    deaths = relationship("DeathLog", back_populates="match", cascade="all, delete")
    kills = relationship("KillLog", back_populates="match", cascade="all, delete")
    item_uses = relationship("ItemUserLog", back_populates="match", cascade="all, delete")
    tasks = relationship("TaskCompleteLog", back_populates="match", cascade="all, delete")
    purchases = relationship("ShopPurchaseLog", back_populates="match", cascade="all, delete")
    doors = relationship("DoorInteractionLog", back_populates="match", cascade="all, delete")

class MatchPlayer(Base):
    """玩家单局结算表 (用于胜率、出场率、存活率统计)"""
    __tablename__ = "match_players"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.match_id"))
    player_name = Column(String, index=True)
    
    role = Column(String)     
    faction = Column(String)  # 阵营 (如 CIVILIAN, KILLER, NEUTRAL)
    
    is_winner = Column(Boolean)
    end_status = Column(String) # ALIVE / DEAD
    
    match = relationship("Match", back_populates="players")

class DeathLog(Base):
    """死亡流水表 (纯受害者视角)"""
    __tablename__ = "death_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.match_id"))
    
    victim_name = Column(String, index=True)
    victim_faction = Column(String)
    death_reason = Column(String) # 死因 (如 wathe:fell_out_of_train)
    
    match = relationship("Match", back_populates="deaths")

class KillLog(Base):
    """击杀流水表 (含凶手视角，可用于计算 K/D 和 TK)"""
    __tablename__ = "kill_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.match_id"))
    
    killer_name = Column(String, index=True)
    killer_faction = Column(String)
    
    victim_name = Column(String, index=True)
    victim_faction = Column(String)
    
    death_reason = Column(String) # 死因 (如 wathe:knife_stab, wathe:gun_shot)
    
    match = relationship("Match", back_populates="kills")

class ItemUserLog(Base):
    """物品使用记录表"""
    __tablename__ = "item_user_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.match_id"))
    
    player_name = Column(String, index=True)
    item = Column(String)
    target = Column(String, nullable=True) # 使用对象（如果有）
    
    pos_x = Column(Float, nullable=True)
    pos_y = Column(Float, nullable=True)
    pos_z = Column(Float, nullable=True)
    
    match = relationship("Match", back_populates="item_uses")

class TaskCompleteLog(Base):
    """任务完成记录表"""
    __tablename__ = "task_complete_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.match_id"))
    
    player_name = Column(String, index=True)
    task_name = Column(String)
    is_real_task = Column(Boolean) # 只有 CIVILIAN 阵营的任务为 True
    
    match = relationship("Match", back_populates="tasks")

class ShopPurchaseLog(Base):
    """商店购买记录表"""
    __tablename__ = "shop_purchase_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.match_id"))
    
    player_name = Column(String, index=True)
    item = Column(String)
    price_paid = Column(Integer)
    balance_after = Column(Integer)
    
    match = relationship("Match", back_populates="purchases")

class DoorInteractionLog(Base):
    """门交互记录表 (娱乐向)"""
    __tablename__ = "door_interaction_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.match_id"))
    
    player_name = Column(String, index=True)
    door_type = Column(String)
    interaction_type = Column(String) # 如 use_key, use_lockpick, use_crowbar
    success = Column(Boolean)
    
    match = relationship("Match", back_populates="doors")