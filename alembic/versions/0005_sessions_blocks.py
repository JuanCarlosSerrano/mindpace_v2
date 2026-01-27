"""add blocks_json to sessions_catalog

Revision ID: 0005_sessions_blocks
Revises: 0004_session_presets
Create Date: 2026-01-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_sessions_blocks"
down_revision = "0004_session_presets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions_catalog", sa.Column("blocks_json", sa.JSON()))


def downgrade() -> None:
    op.drop_column("sessions_catalog", "blocks_json")
