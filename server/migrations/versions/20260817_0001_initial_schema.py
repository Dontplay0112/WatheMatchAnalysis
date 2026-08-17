"""Initial Wathe match schema.

Revision ID: 20260817_0001
Revises:
Create Date: 2026-08-17
"""

from alembic import op
import sqlalchemy as sa


revision = "20260817_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("match_id", sa.String(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=True),
        sa.Column("game_mode", sa.String(), nullable=True),
        sa.Column("win_status", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("match_id"),
    )
    op.create_table(
        "match_players",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.String(), nullable=True),
        sa.Column("player_name", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("faction", sa.String(), nullable=True),
        sa.Column("is_winner", sa.Boolean(), nullable=True),
        sa.Column("end_status", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_match_players_player_name", "match_players", ["player_name"])
    op.create_table(
        "death_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.String(), nullable=True),
        sa.Column("victim_name", sa.String(), nullable=True),
        sa.Column("victim_faction", sa.String(), nullable=True),
        sa.Column("death_reason", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_death_logs_victim_name", "death_logs", ["victim_name"])
    op.create_table(
        "kill_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.String(), nullable=True),
        sa.Column("killer_name", sa.String(), nullable=True),
        sa.Column("killer_faction", sa.String(), nullable=True),
        sa.Column("victim_name", sa.String(), nullable=True),
        sa.Column("victim_faction", sa.String(), nullable=True),
        sa.Column("death_reason", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_kill_logs_killer_name", "kill_logs", ["killer_name"])
    op.create_index("ix_kill_logs_victim_name", "kill_logs", ["victim_name"])
    op.create_table(
        "item_user_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.String(), nullable=True),
        sa.Column("player_name", sa.String(), nullable=True),
        sa.Column("item", sa.String(), nullable=True),
        sa.Column("target", sa.String(), nullable=True),
        sa.Column("pos_x", sa.Float(), nullable=True),
        sa.Column("pos_y", sa.Float(), nullable=True),
        sa.Column("pos_z", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_item_user_logs_player_name", "item_user_logs", ["player_name"])
    op.create_table(
        "task_complete_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.String(), nullable=True),
        sa.Column("player_name", sa.String(), nullable=True),
        sa.Column("task_name", sa.String(), nullable=True),
        sa.Column("is_real_task", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_complete_logs_player_name", "task_complete_logs", ["player_name"])
    op.create_table(
        "shop_purchase_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.String(), nullable=True),
        sa.Column("player_name", sa.String(), nullable=True),
        sa.Column("item", sa.String(), nullable=True),
        sa.Column("price_paid", sa.Integer(), nullable=True),
        sa.Column("balance_after", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shop_purchase_logs_player_name", "shop_purchase_logs", ["player_name"])
    op.create_table(
        "door_interaction_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.String(), nullable=True),
        sa.Column("player_name", sa.String(), nullable=True),
        sa.Column("door_type", sa.String(), nullable=True),
        sa.Column("interaction_type", sa.String(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_door_interaction_logs_player_name", "door_interaction_logs", ["player_name"])


def downgrade() -> None:
    op.drop_index("ix_door_interaction_logs_player_name", table_name="door_interaction_logs")
    op.drop_table("door_interaction_logs")
    op.drop_index("ix_shop_purchase_logs_player_name", table_name="shop_purchase_logs")
    op.drop_table("shop_purchase_logs")
    op.drop_index("ix_task_complete_logs_player_name", table_name="task_complete_logs")
    op.drop_table("task_complete_logs")
    op.drop_index("ix_item_user_logs_player_name", table_name="item_user_logs")
    op.drop_table("item_user_logs")
    op.drop_index("ix_kill_logs_victim_name", table_name="kill_logs")
    op.drop_index("ix_kill_logs_killer_name", table_name="kill_logs")
    op.drop_table("kill_logs")
    op.drop_index("ix_death_logs_victim_name", table_name="death_logs")
    op.drop_table("death_logs")
    op.drop_index("ix_match_players_player_name", table_name="match_players")
    op.drop_table("match_players")
    op.drop_table("matches")
