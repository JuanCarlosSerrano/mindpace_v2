
from __future__ import annotations
from datetime import date
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from sqlalchemy.orm import Session

from src.db.models import EntrenamientoPlanificado


def _dec(x) -> Decimal:
    return Decimal(str(x))


def _q2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _week_key(d) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"

def _parse_fecha_resumen(resumen: str) -> date | None:
    m = re.search(r"Ajuste de sesión \(([^)]+)\)", resumen, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1).strip()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None

def _parse_reduccion_volumen(accion: str) -> tuple[Decimal, Decimal] | None:
    """
    Extrae (from_km, to_km) de:
    'Reducir volumen de 63.0 km a 53.5 km'
    """
    m = re.search(r"Reducir volumen de ([0-9.]+) km a ([0-9.]+) km", accion, re.IGNORECASE)
    if not m:
        return None
    return Decimal(m.group(1)), Decimal(m.group(2))

def _snapshot_entreno(e: EntrenamientoPlanificado) -> dict:
    return {
        "id": e.id,
        "plan_id": e.plan_id,
        "fecha": e.fecha.isoformat(),
        "tipo_sesion": e.tipo_sesion,
        "volumen_objetivo": str(e.volumen_objetivo) if e.volumen_objetivo is not None else None,
        "ritmo_objetivo": e.ritmo_objetivo,
        "detalle_series": e.detalle_series,
        "comentarios_entrenador": e.comentarios_entrenador,
    }

def _record_change(changes: dict, e: EntrenamientoPlanificado) -> dict:
    if e.id not in changes:
        changes[e.id] = {
            "entrenamiento_id": e.id,
            "before": _snapshot_entreno(e),
            "after": None,
            "deleted": False,
        }
    return changes[e.id]


def aplicar_ajustes_semanales(session: Session, plan_id: int, recomendaciones: Iterable) -> tuple[dict, list[dict]]:
    """
    Aplica (en BD) los ajustes semanales propuestos por CoachAI.
    Devuelve un resumen con conteos de cambios.
    """
    entrenos = (
        session.query(EntrenamientoPlanificado)
        .filter(EntrenamientoPlanificado.plan_id == plan_id)
        .all()
    )

    # Indexar entrenos por semana ISO
    por_semana: dict[str, list[EntrenamientoPlanificado]] = {}
    for e in entrenos:
        por_semana.setdefault(_week_key(e.fecha), []).append(e)

    cambios = {
        "semanas_tocadas": set(),
        "volumen_reducido_sesiones": 0,
        "intensidad_reducida_sesiones": 0,
        "sesiones_duras_eliminadas": 0,
    }

    action_records: list[dict] = []

    for r in recomendaciones:
        if getattr(r, "tipo", None) != "semanal":
            continue

        semana = r.semana
        acciones = list(r.acciones)

        if semana not in por_semana:
            continue

        week_ents = por_semana[semana]
        cambios["semanas_tocadas"].add(semana)

        action = {
            "plan_id": plan_id,
            "semana": semana,
            "fecha": None,
            "tipo": "semanal",
            "acciones": {
                "resumen": getattr(r, "resumen", None),
                "acciones": acciones,
                "cambios": [],
            },
        }
        changes: dict[int, dict] = {}
        deleted_ids: set[int] = set()

        # 1) Reducir volumen semanal X% (si viene en acciones)
        # Esperamos strings como: "Reducir volumen de 63.0 km a 53.5 km"
        # 1) Reducir volumen semanal
        for a in acciones:

            # Caso A: reducción explícita "de X km a Y km"
            parsed = _parse_reduccion_volumen(a)
            if parsed:
                from_km, to_km = parsed
                if from_km > 0:
                    factor = (to_km / from_km)

                    for e in week_ents:
                        if e.volumen_objetivo is not None:
                            if e.id in deleted_ids:
                                continue
                            change = _record_change(changes, e)
                            e.volumen_objetivo = _q2(_dec(e.volumen_objetivo) * factor)
                            change["after"] = _snapshot_entreno(e)
                            cambios["volumen_reducido_sesiones"] += 1
                continue

            # Caso B (fallback): "Reducir volumen semanal un 10%"
            if "reducir volumen semanal un 10%" in a.lower():
                factor = Decimal("0.90")
                for e in week_ents:
                    if e.volumen_objetivo is not None:
                        if e.id in deleted_ids:
                            continue
                        change = _record_change(changes, e)
                        e.volumen_objetivo = _q2(_dec(e.volumen_objetivo) * factor)
                        change["after"] = _snapshot_entreno(e)
                        cambios["volumen_reducido_sesiones"] += 1


        # 2) Eliminar 1 sesión dura (si viene)
        # v1: borrar la primera sesión "series" de esa semana
        if any(("eliminar" in a.lower() and "sesión" in a.lower() and "dura" in a.lower()) for a in acciones):
            for e in week_ents:
                if (e.tipo_sesion or "").lower() in ("series", "tempo", "umbral"):
                    change = _record_change(changes, e)
                    change["deleted"] = True
                    deleted_ids.add(e.id)
                    session.delete(e)
                    cambios["sesiones_duras_eliminadas"] += 1
                    break
                # extra v1: si es descarga, también baja volumen un 10% en sesiones con volumen
            for e in week_ents:
                if e.volumen_objetivo is not None:
                    if e.id in deleted_ids:
                        continue
                    change = _record_change(changes, e)
                    e.volumen_objetivo = _q2(_dec(e.volumen_objetivo) * Decimal("0.90"))
                    change["after"] = _snapshot_entreno(e)
                    cambios["volumen_reducido_sesiones"] += 1

        # 3) Semana marcada como descarga
        # v1: si existe sesión dura, bajar ritmo_objetivo (más conservador)
        if any("descarga" in a.lower() for a in acciones):
            for e in week_ents:
                if e.ritmo_objetivo is not None:
                    if e.id in deleted_ids:
                        continue
                    change = _record_change(changes, e)
                    # +10s/km conservador
                    e.ritmo_objetivo = int(e.ritmo_objetivo) + 10
                    change["after"] = _snapshot_entreno(e)
                    cambios["intensidad_reducida_sesiones"] += 1
        if changes:
            action["acciones"]["cambios"] = list(changes.values())
            action_records.append(action)

    session.commit()
    cambios["semanas_tocadas"] = sorted(cambios["semanas_tocadas"])
    return cambios, action_records


def aplicar_ajustes_diarios(session: Session, plan_id: int, recomendaciones: Iterable) -> tuple[dict, list[dict]]:
    """
    Aplica (en BD) los ajustes diarios propuestos por CoachAI.
    Devuelve un resumen con conteos de cambios.
    """
    entrenos = (
        session.query(EntrenamientoPlanificado)
        .filter(EntrenamientoPlanificado.plan_id == plan_id)
        .all()
    )

    por_fecha: dict[date, list[EntrenamientoPlanificado]] = {}
    for e in entrenos:
        por_fecha.setdefault(e.fecha, []).append(e)

    cambios = {
        "fechas_tocadas": set(),
        "sesiones_tocadas": set(),
        "volumen_reducido_sesiones": 0,
        "intensidad_reducida_sesiones": 0,
    }

    action_records: list[dict] = []

    for r in recomendaciones:
        if getattr(r, "tipo", None) != "diaria":
            continue

        fecha = getattr(r, "fecha", None) or _parse_fecha_resumen(getattr(r, "resumen", ""))
        if fecha is None or fecha not in por_fecha:
            continue

        acciones = list(r.acciones)
        cambios["fechas_tocadas"].add(fecha)

        action = {
            "plan_id": plan_id,
            "semana": _week_key(fecha),
            "fecha": fecha,
            "tipo": "diaria",
            "acciones": {
                "resumen": getattr(r, "resumen", None),
                "acciones": acciones,
                "cambios": [],
            },
        }
        changes: dict[int, dict] = {}

        for e in por_fecha[fecha]:
            changed = False
            for a in acciones:
                parsed = _parse_reduccion_volumen(a)
                if parsed:
                    _, to_km = parsed
                    if e.volumen_objetivo is not None:
                        change = _record_change(changes, e)
                        e.volumen_objetivo = _q2(to_km)
                        change["after"] = _snapshot_entreno(e)
                        cambios["volumen_reducido_sesiones"] += 1
                        changed = True
                    continue

                if "reducir intensidad" in a.lower():
                    if e.ritmo_objetivo is not None:
                        change = _record_change(changes, e)
                        e.ritmo_objetivo = int(e.ritmo_objetivo) + 10
                        change["after"] = _snapshot_entreno(e)
                        cambios["intensidad_reducida_sesiones"] += 1
                        changed = True

            if changed:
                cambios["sesiones_tocadas"].add(e.id)

        if changes:
            action["acciones"]["cambios"] = list(changes.values())
            action_records.append(action)

    session.commit()
    cambios["fechas_tocadas"] = sorted(cambios["fechas_tocadas"])
    cambios["sesiones_tocadas"] = len(cambios["sesiones_tocadas"])
    return cambios, action_records
