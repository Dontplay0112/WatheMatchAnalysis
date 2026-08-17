import datetime
import json
import uuid

from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.base_api import BaseAPICommand
from app.core.database import get_db
from app.core.importer import import_match_json
from app.core.paths import MATCHES_DIR, ensure_data_directories

class UploadMatchAPI(BaseAPICommand):
    @property
    def path(self) -> str:
        return "/upload_match"

    @property
    def methods(self) -> list[str]:
        return ["POST"]

    @property
    def requires_player(self) -> bool:
        return False

    async def execute(self, request: Request, db: Session = Depends(get_db)):
        try:
            # 读取 MC 传来的原始 JSON body
            raw_body = await request.body()
            json_str = raw_body.decode('utf-8')
            match_data = json.loads(json_str)

            # 1. 保存到本地 data/matches 文件夹中作为备份
            ensure_data_directories()
            timestamp = match_data.get("startMs")
            if timestamp:
                file_name = datetime.datetime.fromtimestamp(timestamp / 1000).strftime(
                    '%Y-%m-%d_%H-%M-%S'
                )
            else:
                file_name = match_data.get("matchId", str(uuid.uuid4()))
            filepath = MATCHES_DIR / f"{file_name}.json"

            filepath.write_text(json_str, encoding="utf-8")

            # 2. 直接调用解析器存入数据库
            import_match_json(db, str(filepath))

            return {"status": "success", "message": f"对局 {file_name} 录入成功"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
