import datetime
import hashlib
import logging
import re

from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.base_api import BaseAPICommand
from app.core.database import get_db
from app.core.importer import import_match_json, ERROR, EXISTS, SKIPPED
from app.core.paths import MATCHES_DIR, ensure_data_directories
from app.core.security import require_write_token


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
logger = logging.getLogger(__name__)


def _safe_match_filename(match_data: dict) -> str:
    match_id = match_data.get("matchId")
    if not isinstance(match_id, str) or not match_id.strip():
        raise HTTPException(status_code=400, detail="对局数据缺少有效的 matchId")

    timestamp = match_data.get("startMs")
    if timestamp is None:
        time_part = "unknown-time"
    else:
        try:
            time_part = datetime.datetime.fromtimestamp(
                float(timestamp) / 1000,
                tz=datetime.timezone.utc,
            ).strftime("%Y-%m-%d_%H-%M-%S")
        except (TypeError, ValueError, OSError, OverflowError) as exc:
            raise HTTPException(status_code=400, detail="startMs 不是有效时间戳") from exc

    safe_id = re.sub(r"[^A-Za-z0-9._-]", "_", match_id.strip())[:64] or "match"
    digest = hashlib.sha256(match_id.encode("utf-8")).hexdigest()[:10]
    return f"{time_part}_{safe_id}_{digest}.json"

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

    async def execute(
        self,
        request: Request,
        db: Session = Depends(get_db),
        _authorized: None = Depends(require_write_token),
    ):
        try:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail="对局数据超过 10 MiB 限制")
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail="Content-Length 无效") from exc

            # 读取 MC 传来的原始 JSON body
            raw_body = await request.body()
            if len(raw_body) > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="对局数据超过 10 MiB 限制")
            try:
                json_str = raw_body.decode('utf-8')
                match_data = json.loads(json_str)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise HTTPException(status_code=400, detail="请求体不是有效的 UTF-8 JSON") from exc
            if not isinstance(match_data, dict):
                raise HTTPException(status_code=400, detail="对局 JSON 顶层必须是对象")

            # 1. 保存到本地 data/matches 文件夹中作为备份
            ensure_data_directories()
            filename = _safe_match_filename(match_data)
            filepath = MATCHES_DIR / filename
            
            filepath.write_text(json_str, encoding="utf-8")
            
            # 2. 直接调用解析器存入数据库
            result = import_match_json(db, str(filepath))
            if result == ERROR:
                raise HTTPException(status_code=400, detail="对局数据缺少必要字段")
            if result == SKIPPED:
                return {"status": "skipped", "message": "非 wathe:murder 对局，已保存但未入库"}
            if result == EXISTS:
                return {"status": "exists", "message": "对局已存在，未重复入库"}

            return {"status": "success", "message": f"对局 {match_data['matchId']} 录入成功"}
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("录入对局时发生未处理异常")
            raise HTTPException(status_code=500, detail="对局录入失败") from exc
