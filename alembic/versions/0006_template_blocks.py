"""add blocks_json to plantillas_sesiones

Revision ID: 0006_template_blocks
Revises: 0005_sessions_blocks
Create Date: 2026-01-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_template_blocks"
down_revision = "0005_sessions_blocks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plantillas_sesiones", sa.Column("blocks_json", sa.JSON()))


def downgrade() -> None:
    op.drop_column("plantillas_sesiones", "blocks_json")
