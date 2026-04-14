import json
import inspect
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import MatchPlayer
from app.core.base_api import BaseAPICommand

class APIManager:
    def __init__(self):
        self.router = APIRouter()
        self.query_actions = {}

        # 统一注入网关路由 
        self.router.add_api_route(
            path="",
            endpoint=self.unified_query_gateway,
            methods=["POST"],
            name="UnifiedQueryGateway"
        )

    def register(self, command_instance: BaseAPICommand):
        # 根据是否提供 action 决定注册方式
        if command_instance.action:
            for act in command_instance.action:
                self.query_actions[act] = command_instance
        elif command_instance.path:
            # 正常的 RESTful API (如 /refresh, /upload_match)
            self.router.add_api_route(
                path=command_instance.path,
                endpoint=command_instance.execute,
                methods=command_instance.methods,
                name=command_instance.__class__.__name__
            )
        else:
            raise ValueError("注册的 API 实例必须提供 'action' 或 'path' 属性")

    async def unified_query_gateway(self, request: Request, db: Session = Depends(get_db)):
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        action = data.get("action", "help").lower() or "help"
        player_name = data.get("player_name", "")
        faction = data.get("faction", "")

        if action == "help":
            return {"reply": self._handle_help()}

        handler = self.query_actions.get(action)
        if not handler:
            return {"reply": f"❌ 未知的查询类型: {action}\n\n" + self._handle_help()}

        error_reply = self._validate_player(handler, player_name, db)
        if error_reply:
            return {"reply": error_reply}

        return self._execute_handler(handler, player_name, faction, db)

    def _validate_player(self, handler: BaseAPICommand, player_name: str, db: Session) -> str | None:
        """检查玩家约束，返回错误信息字符或者 None 作为通过"""
        if not handler.requires_player:
            return None

        if not player_name:
            return "❌ 请在指令后加上你要查询的玩家名，或者先使用 .wathe bind 绑定账号！"

        if not db.query(MatchPlayer.id).filter(MatchPlayer.player_name == player_name).first():
            return f"❌ 找不到玩家【{player_name}】的对局记录。"

        return None

    def _execute_handler(self, handler: BaseAPICommand, player_name: str, faction: str, db: Session) -> dict:
        try:
            # 仅传入命令 execute 明确声明过的参数，避免影响历史命令签名
            signature = inspect.signature(handler.execute)
            params = signature.parameters

            kwargs = {}
            if "db" in params:
                kwargs["db"] = db
            if "player_name" in params:
                kwargs["player_name"] = player_name
            if "faction" in params:
                kwargs["faction"] = faction

            return handler.execute(**kwargs)
        except Exception as e:
            return {"reply": f"❌ 查询后端时发生异常: {str(e)}"}

    def _handle_help(self) -> str:
        help_text = (
            "📜 列车杀手 数据查询 📜\n"
            "----------------------\n"
            "用法: .wathe [指令] [游戏ID]\n[指令]列表：\n"
        )
        
        # 为了避免别名重复显示，我们记录已经显示过的实例
        all_instances = set()  # 记录所有实例，避免重复显示
        need_player_instances = set()  # 记录需要玩家ID的指令实例
        other_instances = set()  # 记录不需要玩家ID的指令实例
        for act, handler in self.query_actions.items():
            if handler in all_instances:
                continue
            all_instances.add(handler)
            if handler.requires_player:
                need_player_instances.add(handler)
            else:
                other_instances.add(handler)
        # 再展示不需要玩家ID的指令
        for handler in other_instances:
            main_action = handler.action[0]
            aliases = handler.action[1:]
            desc = handler.description
            
            cmd_display = main_action
            if aliases:
                cmd_display += f"({','.join(aliases)})"
                
            help_text += f"  {cmd_display:<12} - {desc}\n"
            
        # 先展示需要玩家ID的指令
        for handler in need_player_instances:
            main_action = handler.action[0]
            aliases = handler.action[1:]
            desc = handler.description
            
            cmd_display = main_action
            if aliases:
                cmd_display += f"({','.join(aliases)})"
                
            help_text += f"  {cmd_display:<12} - {desc} (需要游戏ID或绑定账号)\n"
        
        # # 为了避免别名重复显示，我们记录已经显示过的实例
        # shown_instances = set()
        # for act, handler in self.query_actions.items():
        #     if handler in shown_instances:
        #         continue
        #     shown_instances.add(handler)
            
        #     # 使用主指令名称展示，如果有别名也可以提示
        #     main_action = handler.action[0]
        #     aliases = handler.action[1:]
        #     desc = handler.description
            
        #     cmd_display = main_action
        #     if aliases:
        #         cmd_display += f"({','.join(aliases)})"
                
        #     help_text += f"  {cmd_display:<12} - {desc}\n"
            
        help_text += "  help         - ❓ 查看本帮助菜单\n"
        help_text += "（PS: 游戏ID为空时，默认查询已绑定的账号。\n"
        help_text += "\n----------------------\n"
        return help_text