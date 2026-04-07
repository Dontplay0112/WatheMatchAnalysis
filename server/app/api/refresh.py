from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.base_api import BaseAPICommand
from app.core.database import get_db
from app.core.importer import scan_and_import_all

class RefreshAPI(BaseAPICommand):
    @property
    def path(self) -> str:
        return "/refresh"

    def execute(self, db: Session = Depends(get_db)):
        try:
            scan_and_import_all(db)
            return {"status": "success", "message": "数据库已同步最新对局文件！"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))