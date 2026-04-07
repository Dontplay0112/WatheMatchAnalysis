from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.database import engine, SessionLocal
from app.core.models import Base
from app.core.api_manager import APIManager
from app.core.importer import scan_and_import_all

from app.api.state import StatsAPI
from app.api.roles import RolesAPI
from app.api.deaths import DeathsAPI
from app.api.refresh import RefreshAPI
from app.api.upload import UploadMatchAPI
from app.api.leaderboards import WinRateAPI, DeathRateAPI, KDRatioAPI, XiaonaoAPI
from app.api.nemesis import KilledByAPI, KillingAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        scan_and_import_all(db)
    finally:
        db.close()
    yield

app = FastAPI(title="Wathe Backend", lifespan=lifespan)

api_manager = APIManager()
api_manager.register(StatsAPI())
api_manager.register(RolesAPI())
api_manager.register(DeathsAPI())
api_manager.register(RefreshAPI())
api_manager.register(UploadMatchAPI())
api_manager.register(WinRateAPI())
api_manager.register(DeathRateAPI())
api_manager.register(KDRatioAPI())
api_manager.register(XiaonaoAPI())
api_manager.register(KilledByAPI())
api_manager.register(KillingAPI())

app.include_router(api_manager.router, prefix="/api")