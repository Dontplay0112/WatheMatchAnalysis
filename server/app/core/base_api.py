from abc import ABC, abstractmethod

class BaseAPICommand(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs):
        """执行具体的API逻辑"""
        pass

    @property
    def path(self) -> str | None:
        """API路径，针对独立 RESTful API，如果提供 action，则作为 /query 网关指令"""
        return None

    @property
    def methods(self) -> list[str]:
        """允许的请求方法，默认 GET"""
        return ["GET"]

    @property
    def action(self) -> list[str] | None:
        """Query指令名列表，第一个为主指令，后续为别名。例如 ["stats", "st"]"""
        return None

    @property
    def description(self) -> str | None:
        """Query指令的帮助菜单说明"""
        return None

    @property
    def requires_player(self) -> bool:
        """是否需要强制要求 player_name，默认 True"""
        return True