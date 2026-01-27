from __future__ import annotations
from datetime import date, timedelta
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
from src.db.models import (
    Atleta, PlantillaPlan, PlantillaSesion,
    PlanAtleta, EntrenamientoPlanificado
)

from .rules import (
    AthleteContext,
    ajustar_volumen_sesion,
    ritmo_objetivo_por_vam,
    limitar_intensidad_menores
)
from src.planning.calendar import (
    fecha_lunes_semana,
    fecha_por_semana_y_dia,
)

from src.planning.rules import (
    aplicar_descarga,
)


def calcular_edad(fecha_nacimiento: date | None, hoy: date) -> int | None:
    if not fecha_nacimiento:
        return None
    years = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        years -= 1
    return years


def generar_plan_desde_plantilla(
    session: Session,
    atleta_id: int,
    plantilla_id: int,
    fecha_inicio: date,
    objetivo_descripcion: str = "",
) -> int:
    """
    Genera un PlanAtleta y sus EntrenamientosPlanificados a partir de PlantillaSesion.

    Devuelve: plan_id
    """
    atleta: Atleta | None = session.get(Atleta, atleta_id)
    if not atleta:
        raise ValueError(f"No existe atleta_id={atleta_id}")

    plantilla: PlantillaPlan | None = session.get(PlantillaPlan, plantilla_id)
    if not plantilla:
        raise ValueError(f"No existe plantilla_id={plantilla_id}")

    hoy = date.today()
    edad = calcular_edad(atleta.fecha_nacimiento, hoy)

    ctx = AthleteContext(
        edad=edad,
        volumen_actual_km=float(atleta.volumen_actual_km) if atleta.volumen_actual_km is not None else None,
        vam=float(atleta.vam) if atleta.vam is not None else None
    )

    # Crear plan
    fecha_fin = fecha_inicio + timedelta(weeks=int(plantilla.duracion_semanas or 0)) - timedelta(days=1)

    plan = PlanAtleta(
        atleta_id=atleta.id,
        plantilla_id=plantilla.id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin if plantilla.duracion_semanas else None,
        objetivo_descripcion=objetivo_descripcion,
        estado="activo",
    )
    session.add(plan)
    session.flush()  # obtiene plan.id sin commit

    # Cargar sesiones plantilla (ordenadas)
    sesiones = (
        session.query(PlantillaSesion)
        .filter(PlantillaSesion.plantilla_id == plantilla.id)
        .order_by(PlantillaSesion.semana.asc(), PlantillaSesion.dia_semana.asc())
        .all()
    )
    if not sesiones:
        raise ValueError("La plantilla no tiene sesiones asociadas")

    # Expandir a fechas
    # Convención: semana=1 empieza en fecha_inicio. dia_semana: 1=Lunes ... 7=Domingo.
    # Calculamos la fecha de lunes de la semana 1 a partir de fecha_inicio:
    # Si fecha_inicio cae en otro día, respetamos como "día 1" de la semana 1 igualmente.
    # Simplificación v1: fecha = fecha_inicio + (semana-1)*7 + (dia_semana-1)
    for s in sesiones:
        tipo = s.tipo_sesion or ""
        intensidad = limitar_intensidad_menores(
            float(s.intensidad_pct_vam) if s.intensidad_pct_vam is not None else None,
            ctx
        )
       
        raw_volumen_float = ajustar_volumen_sesion(
            float(s.volumen_base) if s.volumen_base is not None else None,
            ctx
        )

        # Convertimos a Decimal JUSTO AQUÍ
        raw_volumen = (
            Decimal(str(raw_volumen_float))
            if raw_volumen_float is not None
            else None
        )

        raw_volumen = aplicar_descarga(raw_volumen, int(s.semana))

        # 🔒 Normalización FINAL: km reales
        volumen_obj = (
            raw_volumen.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if raw_volumen is not None
            else None
        )   
        
        volumen_obj = aplicar_descarga(volumen_obj, int(s.semana))
        
        ritmo_obj = ritmo_objetivo_por_vam(ctx.vam, tipo)

        lunes_semana_1 = fecha_lunes_semana(fecha_inicio)

        fecha_sesion = fecha_por_semana_y_dia(
            lunes_semana_1,
            int(s.semana),
            int(s.dia_semana),
        )

        entreno = EntrenamientoPlanificado(
            plan_id=plan.id,
            fecha=fecha_sesion,
            tipo_sesion=tipo,
            volumen_objetivo=volumen_obj,
            ritmo_objetivo=ritmo_obj,
            detalle_series=s.formato_series,
            blocks_json=s.blocks_json or [],
            comentarios_entrenador=None,
        )
        session.add(entreno)

    session.commit()
    return plan.id
