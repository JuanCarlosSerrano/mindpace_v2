"""add session presets

Revision ID: 0004_session_presets
Revises: 0003_sessions_catalog
Create Date: 2026-01-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_session_presets"
down_revision = "0003_sessions_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_presets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entrenador_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("tipo_sesion", sa.String(length=50)),
        sa.Column("volumen_base", sa.DECIMAL(6, 2)),
        sa.Column("intensidad_pct_vam", sa.DECIMAL(5, 2)),
        sa.Column("formato_series", sa.String(length=100)),
        sa.Column("recuperacion_seg", sa.Integer()),
        sa.Column("tags_json", sa.JSON()),
        sa.Column("updated_at", sa.TIMESTAMP()),
    )


def downgrade() -> None:
    op.drop_table("session_presets")
