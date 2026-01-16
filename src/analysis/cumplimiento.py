from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.db.models import ComparacionPlanReal, EntrenamientoPlanificado

SESION_CUMPLIDA_MIN = Decimal("0.90")
SESION_CUMPLIDA_MAX = Decimal("1.10")
SESION_EXCESO_MIN = Decimal("1.20")

PESO_TIPO_SESION = {
    "rodaje": Decimal("1.0"),
    "series": Decimal("1.5"),
    "tempo": Decimal("1.5"),
    "umbral": Decimal("1.5"),
}

SEMANA_CUMPLIDA_MIN_RATIO = Decimal("0.90")
SEMANA_CUMPLIDA_MAX_RATIO = Decimal("1.10")
SEMANA_PARCIAL_MIN_RATIO = Decimal("0.70")
SEMANA_SESIONES_MIN = Decimal("0.80")


def _week_key(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def calcular_cumplimiento_semanal(
    session: Session,
    plan_id: int,
    atleta_id: int,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
) -> dict[str, dict]:
    plan_q = session.query(EntrenamientoPlanificado).filter(
        EntrenamientoPlanificado.plan_id == plan_id
    )
    if fecha_inicio:
        plan_q = plan_q.filter(EntrenamientoPlanificado.fecha >= fecha_inicio)
    if fecha_fin:
        plan_q = plan_q.filter(EntrenamientoPlanificado.fecha <= fecha_fin)
    planificados = plan_q.all()

    comp_q = session.query(ComparacionPlanReal).filter(
        ComparacionPlanReal.plan_id == plan_id,
        ComparacionPlanReal.atleta_id == atleta_id,
    )
    if fecha_inicio:
        comp_q = comp_q.filter(ComparacionPlanReal.fecha >= fecha_inicio)
    if fecha_fin:
        comp_q = comp_q.filter(ComparacionPlanReal.fecha <= fecha_fin)
    comparaciones = comp_q.all()
    comp_por_plan = {c.entrenamiento_planificado_id: c for c in comparaciones}

    semanas: dict[str, dict] = {}
    for p in planificados:
        semana = _week_key(p.fecha)
        item = semanas.setdefault(
            semana,
            {
                "sesiones_planificadas": 0,
                "sesiones_realizadas": 0,
                "ratio_sesiones": None,
                "sesiones_planificadas_peso": Decimal("0"),
                "sesiones_realizadas_peso": Decimal("0"),
                "volumen_planificado": Decimal("0"),
                "volumen_real": Decimal("0"),
                "ratio_volumen": None,
                "sesiones_excesivas": 0,
                "sesiones_excesivas_peso": Decimal("0"),
                "sesiones_no_realizadas": 0,
                "estado": "no_evaluable",
            },
        )
        item["sesiones_planificadas"] += 1
        peso = PESO_TIPO_SESION.get((p.tipo_sesion or "").lower(), Decimal("1.0"))
        item["sesiones_planificadas_peso"] += peso
        if p.volumen_objetivo is not None:
            item["volumen_planificado"] += Decimal(str(p.volumen_objetivo))

        comp = comp_por_plan.get(p.id)
        if comp is None:
            item["sesiones_no_realizadas"] += 1
            continue

        item["sesiones_realizadas"] += 1
        item["sesiones_realizadas_peso"] += peso
        if comp.dist_real_km is not None:
            item["volumen_real"] += Decimal(str(comp.dist_real_km))

        if comp.pct_dist is not None:
            ratio = Decimal(str(comp.pct_dist))
            if ratio > SESION_EXCESO_MIN:
                item["sesiones_excesivas"] += 1
                item["sesiones_excesivas_peso"] += peso

    for semana, item in semanas.items():
        sp = item["sesiones_planificadas"]
        sr = item["sesiones_realizadas"]
        if sp > 0:
            # Ratio ponderado por tipo de sesion (v1).
            peso_plan = item["sesiones_planificadas_peso"]
            peso_real = item["sesiones_realizadas_peso"]
            if peso_plan > 0:
                item["ratio_sesiones"] = (peso_real / peso_plan).quantize(Decimal("0.01"))
            else:
                item["ratio_sesiones"] = (Decimal(sr) / Decimal(sp)).quantize(Decimal("0.01"))

        if item["volumen_planificado"] > 0:
            item["ratio_volumen"] = (
                item["volumen_real"] / item["volumen_planificado"]
            ).quantize(Decimal("0.01"))

        ratio_vol = item["ratio_volumen"]
        ratio_ses = item["ratio_sesiones"]
        excesivas = item["sesiones_excesivas"]
        excesivas_peso = item["sesiones_excesivas_peso"]
        muchas_excesivas = excesivas >= 2 or (
            item["sesiones_planificadas_peso"] > 0
            and excesivas_peso / item["sesiones_planificadas_peso"] >= Decimal("0.30")
        )

        if item["sesiones_realizadas"] == 0 and item["volumen_real"] == 0:
            item["ratio_sesiones"] = None
            item["ratio_volumen"] = None
            item["estado"] = "datos_insuficientes"
        elif ratio_vol is None or ratio_ses is None:
            item["estado"] = "no_evaluable"
        elif ratio_vol > SESION_EXCESO_MIN or muchas_excesivas:
            item["estado"] = "exceso"
        elif ratio_vol < SEMANA_PARCIAL_MIN_RATIO:
            item["estado"] = "bajo_cumplimiento"
        elif (
            SEMANA_CUMPLIDA_MIN_RATIO <= ratio_vol <= SEMANA_CUMPLIDA_MAX_RATIO
            and ratio_ses >= SEMANA_SESIONES_MIN
        ):
            item["estado"] = "cumplida"
        else:
            item["estado"] = "parcial"

        item["volumen_planificado"] = float(item["volumen_planificado"])
        item["volumen_real"] = float(item["volumen_real"])
        item["sesiones_planificadas_peso"] = float(item["sesiones_planificadas_peso"])
        item["sesiones_realizadas_peso"] = float(item["sesiones_realizadas_peso"])
        item["sesiones_excesivas_peso"] = float(item["sesiones_excesivas_peso"])

    return semanas
