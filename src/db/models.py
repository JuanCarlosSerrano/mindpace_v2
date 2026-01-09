from datetime import datetime, date
from sqlalchemy.orm import validates
from decimal import Decimal
from sqlalchemy import (
    String, Integer, Date, Boolean, ForeignKey,
    Enum, Text, DECIMAL, TIMESTAMP, JSON
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(
        Enum("admin", "entrenador", "atleta", name="rol_usuario"),
        nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_alta: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )

    atleta = relationship(
        "Atleta",
        uselist=False,
        foreign_keys="[Atleta.usuario_id]",
        back_populates="usuario"
    )

    atletas_entrenados = relationship(
        "Atleta",
        foreign_keys="[Atleta.entrenador_id]"
    )

class Atleta(Base):
    __tablename__ = "atletas"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    entrenador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)

    fecha_nacimiento: Mapped[Date | None] = mapped_column(Date)
    sexo: Mapped[str | None] = mapped_column(
        Enum("M", "F", "O", name="sexo_atleta")
    )
    altura_cm: Mapped[int | None]
    peso_kg: Mapped[float | None] = mapped_column(DECIMAL(5, 2))

    experiencia_anios: Mapped[int | None]
    dias_entreno_semana: Mapped[int | None]

    volumen_actual_km: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    vam: Mapped[float | None] = mapped_column(DECIMAL(4, 2))
    ritmo_umbral: Mapped[int | None]

    categoria: Mapped[str | None] = mapped_column(String(50))

    usuario = relationship(
        "Usuario",
        foreign_keys="[Atleta.usuario_id]",
        back_populates="atleta"
    )

    entrenador = relationship(
        "Usuario",
        foreign_keys="[Atleta.entrenador_id]",
        overlaps="atletas_entrenados"
    )

    planes = relationship("PlanAtleta", back_populates="atleta")
class PlantillaPlan(Base):
    __tablename__ = "plantillas_plan"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    distancia_objetivo: Mapped[str | None] = mapped_column(String(20))
    nivel: Mapped[str | None] = mapped_column(
        Enum("base", "intermedio", "avanzado", name="nivel_plan")
    )
    duracion_semanas: Mapped[int | None]
    metodo: Mapped[str | None] = mapped_column(String(50))

    sesiones = relationship("PlantillaSesion", back_populates="plantilla")
class PlantillaSesion(Base):
    __tablename__ = "plantillas_sesiones"

    id: Mapped[int] = mapped_column(primary_key=True)
    plantilla_id: Mapped[int] = mapped_column(ForeignKey("plantillas_plan.id"))
    semana: Mapped[int]
    dia_semana: Mapped[int]

    tipo_sesion: Mapped[str | None] = mapped_column(String(50))
    volumen_base: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    intensidad_pct_vam: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    formato_series: Mapped[str | None] = mapped_column(String(100))
    recuperacion_seg: Mapped[int | None]

    plantilla = relationship("PlantillaPlan", back_populates="sesiones")
class PlanAtleta(Base):
    __tablename__ = "planes_atleta"

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atletas.id"))
    plantilla_id: Mapped[int] = mapped_column(ForeignKey("plantillas_plan.id"))

    fecha_inicio: Mapped[Date | None] = mapped_column(Date)
    fecha_fin: Mapped[Date | None] = mapped_column(Date)
    objetivo_descripcion: Mapped[str | None] = mapped_column(Text)

    estado: Mapped[str] = mapped_column(
        Enum("activo", "completado", "cancelado", name="estado_plan"),
        default="activo"
    )

    atleta = relationship("Atleta", back_populates="planes")
    plantilla = relationship("PlantillaPlan")
    entrenamientos = relationship("EntrenamientoPlanificado", back_populates="plan")
class EntrenamientoPlanificado(Base):
    __tablename__ = "entrenamientos_planificados"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("planes_atleta.id"))
    fecha: Mapped[Date] = mapped_column(Date)
    tipo_sesion: Mapped[str | None] = mapped_column(String(50))
    volumen_objetivo: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    ritmo_objetivo: Mapped[int | None]
    detalle_series: Mapped[str | None] = mapped_column(String(150))
    comentarios_entrenador: Mapped[str | None] = mapped_column(Text)
    realizado_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "entrenamientos_realizados.id",
            use_alter=True,
            name="fk_planificado_realizado_id",
        )
    )
    
    # 🔒 CORTAFUEGOS DE UNIDADES
    @validates("volumen_objetivo")
    def validate_volumen_objetivo(self, key, value):
        if value is None:
            return value

        v = Decimal(str(value))

        if v < 0:
            raise ValueError("volumen_objetivo no puede ser negativo")

        if v > Decimal("60"):
            raise ValueError(
                f"volumen_objetivo={v} km no es razonable para una sesión. "
                "¿Error de unidades? (esperado km reales)"
            )

        return v
    plan = relationship("PlanAtleta", back_populates="entrenamientos")
class EntrenamientoRealizado(Base):
    __tablename__ = "entrenamientos_realizados"

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atletas.id"))
    fecha: Mapped[Date] = mapped_column(Date)

    origen: Mapped[str | None] = mapped_column(
        Enum("manual", "strava", "garmin", "polar", name="origen_entreno")
    )
    tipo_sesion: Mapped[str | None] = mapped_column(String(20))
    actividad_id_externa: Mapped[str | None] = mapped_column(String(100))

    distancia_km: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    tiempo_seg: Mapped[int | None]
    ritmo_medio: Mapped[int | None]
    fc_media: Mapped[int | None]
    fc_max: Mapped[int | None]
    desnivel_m: Mapped[int | None]

    sensacion: Mapped[int | None]
    comentarios: Mapped[str | None] = mapped_column(Text)
    planificado_id: Mapped[int | None] = mapped_column(
        ForeignKey("entrenamientos_planificados.id")
    )
    match_confianza: Mapped[float | None] = mapped_column(DECIMAL(4, 2))
    match_metodo: Mapped[str | None] = mapped_column(String(20))
class ComparacionPlanReal(Base):
    __tablename__ = "comparacion_plan_real"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("planes_atleta.id"))
    atleta_id: Mapped[int | None] = mapped_column(ForeignKey("atletas.id"))
    fecha: Mapped[Date | None] = mapped_column(Date)
    entrenamiento_planificado_id: Mapped[int] = mapped_column(
        ForeignKey("entrenamientos_planificados.id")
    )
    entrenamiento_realizado_id: Mapped[int] = mapped_column(
        ForeignKey("entrenamientos_realizados.id")
    )

    dist_plan_km: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    dist_real_km: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    pct_dist: Mapped[float | None] = mapped_column(DECIMAL(5, 2))

    ritmo_plan: Mapped[int | None]
    ritmo_real: Mapped[int | None]
    delta_ritmo: Mapped[int | None]

    sensacion: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )

    cumplimiento_pct: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    desviacion_volumen: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    desviacion_ritmo: Mapped[int | None]

    estado: Mapped[str | None] = mapped_column(
        Enum("ok", "ajustado", "fallido", name="estado_comparacion")
    )
class MetricaAtleta(Base):
    __tablename__ = "metricas_atleta"

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atletas.id"))
    fecha: Mapped[Date] = mapped_column(Date)

    carga_semanal: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    fatiga_estimada: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    tendencia_rendimiento: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    riesgo_lesion: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
class Recomendacion(Base):
    __tablename__ = "recomendaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atletas.id"))
    fecha: Mapped[Date] = mapped_column(Date)

    tipo: Mapped[str | None] = mapped_column(String(50))
    descripcion: Mapped[str | None] = mapped_column(Text)
    nivel_confianza: Mapped[float | None] = mapped_column(DECIMAL(4, 2))

    aplicada: Mapped[bool] = mapped_column(Boolean, default=False)

class CoachAction(Base):
    __tablename__ = "coach_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("planes_atleta.id"))
    semana: Mapped[str | None] = mapped_column(String(10))
    fecha: Mapped[Date | None] = mapped_column(Date)
    tipo: Mapped[str] = mapped_column(
        Enum("semanal", "diaria", "reversion", name="tipo_coach_action"),
        nullable=False
    )
    acciones: Mapped[dict | list] = mapped_column(JSON, nullable=False)
    estado: Mapped[str] = mapped_column(
        Enum("aplicada", "revertida", name="estado_coach_action"),
        default="aplicada"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )
