import logging

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.base_api import BaseAPICommand
from app.core.database import get_db
from app.core.importer import scan_and_import_all
from app.core.security import require_write_token


logger = logging.getLogger(__name__)

class RefreshAPI(BaseAPICommand):
    @property
    def path(self) -> str:
        return "/refresh"

    def execute(
        self,
        db: Session = Depends(get_db),
        _authorized: None = Depends(require_write_token),
    ):
        try:
            scan_and_import_all(db)
            return {"status": "success", "message": "数据库已同步最新对局文件！"}
        except Exception as exc:
            logger.exception("手动刷新对局数据失败")
            raise HTTPException(status_code=500, detail="数据库刷新失败") from exc
