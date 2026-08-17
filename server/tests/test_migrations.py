from alembic import command
from sqlalchemy import create_engine, inspect

from app.core.migrations import migration_config, run_migrations
from app.core.models import Base, Match


def test_initial_migration_builds_complete_schema(tmp_path):
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    config = migration_config(database_url)
    command.upgrade(config, "head")
    command.check(config)

    tables = set(inspect(create_engine(database_url)).get_table_names())
    assert {
        "alembic_version",
        "matches",
        "match_players",
        "death_logs",
        "kill_logs",
        "item_user_logs",
        "task_complete_logs",
        "shop_purchase_logs",
        "door_interaction_logs",
    } <= tables


def test_existing_database_is_stamped_without_losing_data(tmp_path):
    database_path = tmp_path / "legacy.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            Match.__table__.insert().values(
                match_id="existing-match",
                game_mode="wathe:murder",
            )
        )

    run_migrations(engine, database_url)

    inspector = inspect(engine)
    assert "alembic_version" in inspector.get_table_names()
    with engine.connect() as connection:
        assert connection.execute(
            Match.__table__.select().where(Match.match_id == "existing-match")
        ).first() is not None
