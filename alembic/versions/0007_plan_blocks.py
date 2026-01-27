"""add blocks_json to entrenamientos_planificados

Revision ID: 0007_plan_blocks
Revises: 0006_template_blocks
Create Date: 2026-01-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_plan_blocks"
down_revision = "0006_template_blocks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("entrenamientos_planificados", sa.Column("blocks_json", sa.JSON()))


def downgrade() -> None:
    op.drop_column("entrenamientos_planificados", "blocks_json")
