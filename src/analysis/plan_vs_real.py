from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from src.db.models import (
    ComparacionPlanReal,
    EntrenamientoPlanificado,
    EntrenamientoRealizado,
    PlanAtleta,
)


def _dec(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _q2(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calc_ritmo_real(entreno: EntrenamientoRealizado) -> int | None:
    if entreno.ritmo_medio is not None:
        return int(entreno.ritmo_medio)
    if entreno.tiempo_seg is None or entreno.distancia_km is None:
        return None
    dist = _dec(entreno.distancia_km)
    if dist is None or dist <= 0:
        return None
    return int(Decimal(entreno.tiempo_seg) / dist)


def generar_comparacion_plan_real(
    session: Session,
    plan_id: int,
    atleta_id: int,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    persist: bool = True,
) -> dict:
    q = (
        session.query(EntrenamientoRealizado)
        .filter(EntrenamientoRealizado.atleta_id == atleta_id)
        .filter(EntrenamientoRealizado.planificado_id.isnot(None))
    )
    if fecha_inicio:
        q = q.filter(EntrenamientoRealizado.fecha >= fecha_inicio)
    if fecha_fin:
        q = q.filter(EntrenamientoRealizado.fecha <= fecha_fin)

    realizados = q.all()

    resumen = {
        "insertados": 0,
        "actualizados": 0,
        "ignorados": 0,
        "ignored_details": [],
    }

    for r in realizados:
        planificado = session.get(EntrenamientoPlanificado, r.planificado_id)
        if planificado is None:
            resumen["ignorados"] += 1
            resumen["ignored_details"].append(
                {
                    "real_id": r.id,
                    "planificado_id": r.planificado_id,
                    "plan_id_del_planificado": None,
                    "plan_id_objetivo": plan_id,
                    "motivo": "planificado_no_encontrado",
                }
            )
            continue
        if planificado.plan_id != plan_id:
            resumen["ignorados"] += 1
            resumen["ignored_details"].append(
                {
                    "real_id": r.id,
                    "planificado_id": planificado.id,
                    "plan_id_del_planificado": planificado.plan_id,
                    "plan_id_objetivo": plan_id,
                    "motivo": "plan_distinto",
                }
            )
            continue

        comparacion = (
            session.query(ComparacionPlanReal)
            .filter(
                ComparacionPlanReal.entrenamiento_planificado_id == planificado.id,
                ComparacionPlanReal.entrenamiento_realizado_id == r.id,
            )
            .first()
        )

        dist_plan = _dec(planificado.volumen_objetivo)
        dist_real = _dec(r.distancia_km)
        pct_dist = None
        if dist_plan is not None and dist_plan > 0 and dist_real is not None:
            pct_dist = _q2(dist_real / dist_plan)

        ritmo_real = _calc_ritmo_real(r)
        ritmo_plan = planificado.ritmo_objetivo
        delta_ritmo = None
        if ritmo_plan is not None and ritmo_real is not None:
            delta_ritmo = int(ritmo_real) - int(ritmo_plan)

        if comparacion is None:
            comparacion = ComparacionPlanReal(
                plan_id=plan_id,
                atleta_id=atleta_id,
                fecha=r.fecha,
                entrenamiento_planificado_id=planificado.id,
                entrenamiento_realizado_id=r.id,
            )
            session.add(comparacion)
            resumen["insertados"] += 1
        else:
            resumen["actualizados"] += 1

        comparacion.dist_plan_km = dist_plan
        comparacion.dist_real_km = dist_real
        comparacion.pct_dist = pct_dist
        comparacion.ritmo_plan = ritmo_plan
        comparacion.ritmo_real = ritmo_real
        comparacion.delta_ritmo = delta_ritmo
        comparacion.sensacion = r.sensacion

    if persist:
        session.commit()

    return resumen


def obtener_resumen_cumplimiento_semanal(
    session: Session,
    plan_id: int,
    atleta_id: int,
) -> dict:
    plan = session.get(PlanAtleta, plan_id)
    if plan is None:
        return {}

    q = session.query(ComparacionPlanReal).filter(
        ComparacionPlanReal.plan_id == plan_id,
        ComparacionPlanReal.atleta_id == atleta_id,
    )
    comparaciones = q.all()
    resumen: dict[str, dict] = {}
    for c in comparaciones:
        if not c.fecha:
            continue
        y, w, _ = c.fecha.isocalendar()
        semana = f"{y}-W{w:02d}"
        item = resumen.setdefault(
            semana,
            {"sesiones": 0, "pct_dist_prom": None, "delta_ritmo_prom": None},
        )
        item["sesiones"] += 1

        if c.pct_dist is not None:
            total = item.get("_pct_total", Decimal("0"))
            item["_pct_total"] = total + Decimal(str(c.pct_dist))
        if c.delta_ritmo is not None:
            total = item.get("_delta_total", 0)
            item["_delta_total"] = total + int(c.delta_ritmo)

    for semana, item in resumen.items():
        sesiones = item["sesiones"]
        if sesiones:
            if "_pct_total" in item:
                item["pct_dist_prom"] = _q2(item["_pct_total"] / sesiones)
            if "_delta_total" in item:
                item["delta_ritmo_prom"] = int(item["_delta_total"] / sesiones)
        item.pop("_pct_total", None)
        item.pop("_delta_total", None)
    return resumen
