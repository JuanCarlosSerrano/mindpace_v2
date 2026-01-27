"""sessions catalog

Revision ID: 0003_sessions_catalog
Revises: 0002_templates_catalog
Create Date: 2026-01-16 00:20:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_sessions_catalog"
down_revision = "0002_templates_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions_catalog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tipo_sesion", sa.String(length=50), nullable=True),
        sa.Column("volumen_base", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("intensidad_pct_vam", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("formato_series", sa.String(length=100), nullable=True),
        sa.Column("recuperacion_seg", sa.Integer(), nullable=True),
        sa.Column("tags_json", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sessions_catalog")
