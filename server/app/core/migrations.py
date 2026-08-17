from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.core.database import SQLALCHEMY_DATABASE_URL, engine
from app.core.paths import SERVER_DIR


def migration_config(database_url: str = SQLALCHEMY_DATABASE_URL) -> Config:
    config = Config(str(SERVER_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(SERVER_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def run_migrations(database_engine=engine, database_url: str = SQLALCHEMY_DATABASE_URL) -> None:
    config = migration_config(database_url)
    tables = set(inspect(database_engine).get_table_names())

    # Databases created by older versions already match the baseline schema.
    if "matches" in tables and "alembic_version" not in tables:
        command.stamp(config, "head")
        return

    command.upgrade(config, "head")
