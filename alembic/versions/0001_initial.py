"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-16 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "rol",
            sa.Enum("admin", "entrenador", "atleta", name="rol_usuario"),
            nullable=False,
        ),
        sa.Column("activo", sa.Boolean(), nullable=True),
        sa.Column("fecha_alta", sa.TIMESTAMP(), nullable=True),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "atletas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("entrenador_id", sa.Integer(), nullable=False),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column(
            "sexo", sa.Enum("M", "F", "O", name="sexo_atleta"), nullable=True
        ),
        sa.Column("altura_cm", sa.Integer(), nullable=True),
        sa.Column("peso_kg", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("experiencia_anios", sa.Integer(), nullable=True),
        sa.Column("dias_entreno_semana", sa.Integer(), nullable=True),
        sa.Column("volumen_actual_km", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("vam", sa.DECIMAL(4, 2), nullable=True),
        sa.Column("ritmo_umbral", sa.Integer(), nullable=True),
        sa.Column("categoria", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["entrenador_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
    )

    op.create_table(
        "plantillas_plan",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("distancia_objetivo", sa.String(length=20), nullable=True),
        sa.Column(
            "nivel",
            sa.Enum("base", "intermedio", "avanzado", name="nivel_plan"),
            nullable=True,
        ),
        sa.Column("duracion_semanas", sa.Integer(), nullable=True),
        sa.Column("metodo", sa.String(length=50), nullable=True),
    )

    op.create_table(
        "plantillas_sesiones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plantilla_id", sa.Integer(), nullable=False),
        sa.Column("semana", sa.Integer(), nullable=True),
        sa.Column("dia_semana", sa.Integer(), nullable=True),
        sa.Column("tipo_sesion", sa.String(length=50), nullable=True),
        sa.Column("volumen_base", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("intensidad_pct_vam", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("formato_series", sa.String(length=100), nullable=True),
        sa.Column("recuperacion_seg", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["plantilla_id"], ["plantillas_plan.id"]),
    )

    op.create_table(
        "planes_atleta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("atleta_id", sa.Integer(), nullable=True),
        sa.Column("plantilla_id", sa.Integer(), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("objetivo_descripcion", sa.Text(), nullable=True),
        sa.Column(
            "estado",
            sa.Enum("activo", "completado", "cancelado", name="estado_plan"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["atleta_id"], ["atletas.id"]),
        sa.ForeignKeyConstraint(["plantilla_id"], ["plantillas_plan.id"]),
    )

    op.create_table(
        "entrenamientos_planificados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("tipo_sesion", sa.String(length=50), nullable=True),
        sa.Column("volumen_objetivo", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("ritmo_objetivo", sa.Integer(), nullable=True),
        sa.Column("detalle_series", sa.String(length=150), nullable=True),
        sa.Column("comentarios_entrenador", sa.Text(), nullable=True),
        sa.Column("realizado_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["planes_atleta.id"]),
    )

    op.create_table(
        "entrenamientos_realizados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("atleta_id", sa.Integer(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column(
            "origen",
            sa.Enum("manual", "strava", "garmin", "polar", name="origen_entreno"),
            nullable=True,
        ),
        sa.Column("tipo_sesion", sa.String(length=20), nullable=True),
        sa.Column("actividad_id_externa", sa.String(length=100), nullable=True),
        sa.Column("distancia_km", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("tiempo_seg", sa.Integer(), nullable=True),
        sa.Column("ritmo_medio", sa.Integer(), nullable=True),
        sa.Column("fc_media", sa.Integer(), nullable=True),
        sa.Column("fc_max", sa.Integer(), nullable=True),
        sa.Column("desnivel_m", sa.Integer(), nullable=True),
        sa.Column("sensacion", sa.Integer(), nullable=True),
        sa.Column("comentarios", sa.Text(), nullable=True),
        sa.Column("planificado_id", sa.Integer(), nullable=True),
        sa.Column("match_confianza", sa.DECIMAL(4, 2), nullable=True),
        sa.Column("match_metodo", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["atleta_id"], ["atletas.id"]),
        sa.ForeignKeyConstraint(
            ["planificado_id"], ["entrenamientos_planificados.id"]
        ),
    )

    op.create_foreign_key(
        "fk_planificado_realizado_id",
        "entrenamientos_planificados",
        "entrenamientos_realizados",
        ["realizado_id"],
        ["id"],
        use_alter=True,
    )

    op.create_table(
        "comparacion_plan_real",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("atleta_id", sa.Integer(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("entrenamiento_planificado_id", sa.Integer(), nullable=False),
        sa.Column("entrenamiento_realizado_id", sa.Integer(), nullable=False),
        sa.Column("dist_plan_km", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("dist_real_km", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("pct_dist", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("ritmo_plan", sa.Integer(), nullable=True),
        sa.Column("ritmo_real", sa.Integer(), nullable=True),
        sa.Column("delta_ritmo", sa.Integer(), nullable=True),
        sa.Column("sensacion", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("cumplimiento_pct", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("desviacion_volumen", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("desviacion_ritmo", sa.Integer(), nullable=True),
        sa.Column(
            "estado",
            sa.Enum("ok", "ajustado", "fallido", name="estado_comparacion"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["planes_atleta.id"]),
        sa.ForeignKeyConstraint(["atleta_id"], ["atletas.id"]),
        sa.ForeignKeyConstraint(
            ["entrenamiento_planificado_id"], ["entrenamientos_planificados.id"]
        ),
        sa.ForeignKeyConstraint(
            ["entrenamiento_realizado_id"], ["entrenamientos_realizados.id"]
        ),
    )

    op.create_table(
        "metricas_atleta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("atleta_id", sa.Integer(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("carga_semanal", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("fatiga_estimada", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("tendencia_rendimiento", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("riesgo_lesion", sa.DECIMAL(5, 2), nullable=True),
        sa.ForeignKeyConstraint(["atleta_id"], ["atletas.id"]),
    )

    op.create_table(
        "recomendaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("atleta_id", sa.Integer(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("tipo", sa.String(length=50), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("nivel_confianza", sa.DECIMAL(4, 2), nullable=True),
        sa.Column("aplicada", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["atleta_id"], ["atletas.id"]),
    )

    op.create_table(
        "coach_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("semana", sa.String(length=10), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column(
            "tipo",
            sa.Enum("semanal", "diaria", "reversion", name="tipo_coach_action"),
            nullable=False,
        ),
        sa.Column("acciones", sa.JSON(), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("aplicada", "revertida", name="estado_coach_action"),
            nullable=True,
        ),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["planes_atleta.id"]),
    )

    op.create_table(
        "athlete_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("athlete_id", sa.Integer(), nullable=True),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("session_date", sa.Date(), nullable=True),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column("mood", sa.Integer(), nullable=True),
        sa.Column("fatigue", sa.Integer(), nullable=True),
        sa.Column("soreness", sa.Integer(), nullable=True),
        sa.Column("pain_flag", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["athlete_id"], ["atletas.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["planes_atleta.id"]),
        sa.UniqueConstraint(
            "athlete_id", "session_date", name="uq_feedback_athlete_date"
        ),
    )


def downgrade() -> None:
    op.drop_table("athlete_feedback")
    op.drop_table("coach_actions")
    op.drop_table("recomendaciones")
    op.drop_table("metricas_atleta")
    op.drop_table("comparacion_plan_real")
    op.drop_constraint(
        "fk_planificado_realizado_id",
        "entrenamientos_planificados",
        type_="foreignkey",
    )
    op.drop_table("entrenamientos_realizados")
    op.drop_table("entrenamientos_planificados")
    op.drop_table("planes_atleta")
    op.drop_table("plantillas_sesiones")
    op.drop_table("plantillas_plan")
    op.drop_table("atletas")
    op.drop_table("usuarios")
