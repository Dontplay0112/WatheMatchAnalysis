from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.paths import DATA_DIR, ensure_data_directories


ensure_data_directories()
SQLALCHEMY_DATABASE_URL = f"sqlite:///{(DATA_DIR / 'data.db').as_posix()}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
