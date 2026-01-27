"""templates catalog

Revision ID: 0002_templates_catalog
Revises: 0001_initial
Create Date: 2026-01-16 00:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_templates_catalog"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "templates_catalog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("goal", sa.String(length=50), nullable=True),
        sa.Column("level", sa.String(length=20), nullable=True),
        sa.Column("duration_weeks", sa.Integer(), nullable=True),
        sa.Column("tags_json", sa.JSON(), nullable=True),
        sa.Column("estimated_weekly_load", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("source_key", sa.String(length=50), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("templates_catalog")
