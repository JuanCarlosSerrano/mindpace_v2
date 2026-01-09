from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from src.db.models import EntrenamientoPlanificado, EntrenamientoRealizado, PlanAtleta
from src.planning.backfill_real_tipo import inferir_tipo_desde_texto


def _tipo_compatible(plan_tipo: str | None) -> set[str]:
    if not plan_tipo:
        return set()
    t = plan_tipo.lower()
    if t == "rodaje":
        return {"rodaje"}
    if t in ("series", "tempo", "intervalos", "umbral"):
        return {"series", "tempo", "intervalos", "umbral"}
    return {t}


def _normalizar_tipo_realizado(tipo: str | None) -> str | None:
    if not tipo:
        return None
    t = tipo.lower().strip()
    alias = {
        "easy": "rodaje",
        "intervalos": "series",
        "threshold": "umbral",
    }
    return alias.get(t, t)


def _filtrar_por_tipo(
    candidatos: list[EntrenamientoPlanificado], tipo_real: str | None
) -> list[EntrenamientoPlanificado]:
    if not tipo_real:
        return candidatos
    exactos = [p for p in candidatos if (p.tipo_sesion or "").lower() == tipo_real]
    if exactos:
        return exactos
    compatibles = []
    for p in candidatos:
        tipos = _tipo_compatible(p.tipo_sesion)
        if tipo_real in tipos:
            compatibles.append(p)
    return compatibles or candidatos


def _resolver_por_distancia(
    candidatos: list[EntrenamientoPlanificado], distancia_real
) -> list[EntrenamientoPlanificado]:
    if distancia_real is None or not candidatos:
        return candidatos
    dist = float(distancia_real)
    diffs = []
    for p in candidatos:
        if p.volumen_objetivo is None:
            continue
        diffs.append((abs(float(p.volumen_objetivo) - dist), p))
    if not diffs:
        return candidatos
    diffs.sort(key=lambda x: x[0])
    best_diff = diffs[0][0]
    best = [p for d, p in diffs if d == best_diff]
    return best


def _calc_ritmo_real(entreno: EntrenamientoRealizado) -> int | None:
    if entreno.ritmo_medio is not None:
        return int(entreno.ritmo_medio)
    if entreno.tiempo_seg is None or entreno.distancia_km is None:
        return None
    dist = float(entreno.distancia_km)
    if dist <= 0:
        return None
    return int(entreno.tiempo_seg / dist)


def _resolver_por_ritmo(
    candidatos: list[EntrenamientoPlanificado], ritmo_real: int | None
) -> list[EntrenamientoPlanificado]:
    if ritmo_real is None or not candidatos:
        return candidatos
    diffs = []
    for p in candidatos:
        if p.ritmo_objetivo is None:
            continue
        diffs.append((abs(int(p.ritmo_objetivo) - int(ritmo_real)), p))
    if not diffs:
        return candidatos
    diffs.sort(key=lambda x: x[0])
    best_diff = diffs[0][0]
    best = [p for d, p in diffs if d == best_diff]
    return best


def vincular_real_vs_planificado(
    session: Session,
    atleta_id: int,
    plan_id: int | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    persist: bool = True,
) -> dict:
    q = session.query(EntrenamientoRealizado).filter(
        EntrenamientoRealizado.atleta_id == atleta_id,
        EntrenamientoRealizado.planificado_id.is_(None),
    )
    if fecha_inicio:
        q = q.filter(EntrenamientoRealizado.fecha >= fecha_inicio)
    if fecha_fin:
        q = q.filter(EntrenamientoRealizado.fecha <= fecha_fin)
    realizados = q.order_by(EntrenamientoRealizado.fecha.asc()).all()

    if plan_id is None:
        plan = (
            session.query(PlanAtleta)
            .filter(PlanAtleta.atleta_id == atleta_id)
            .filter(PlanAtleta.estado == "activo")
            .order_by(PlanAtleta.fecha_inicio.desc().nullslast(), PlanAtleta.id.desc())
            .first()
        )
        plan_id = plan.id if plan else None

    plan_q = session.query(EntrenamientoPlanificado).filter(
        EntrenamientoPlanificado.realizado_id.is_(None)
    )
    if plan_id is not None:
        plan_q = plan_q.filter(EntrenamientoPlanificado.plan_id == plan_id)
    else:
        plan_q = plan_q.join(PlanAtleta).filter(PlanAtleta.atleta_id == atleta_id)
    if fecha_inicio:
        plan_q = plan_q.filter(EntrenamientoPlanificado.fecha >= fecha_inicio)
    if fecha_fin:
        plan_q = plan_q.filter(EntrenamientoPlanificado.fecha <= fecha_fin)
    planificados = plan_q.all()

    por_fecha: dict[date, list[EntrenamientoPlanificado]] = {}
    for p in planificados:
        por_fecha.setdefault(p.fecha, []).append(p)

    resumen = {
        "vinculados": 0,
        "no_vinculados": 0,
        "conflictos": 0,
        "detalles": [],
    }

    usados_plan: set[int] = set()

    for r in realizados:
        candidatos = []
        tipo_real = _normalizar_tipo_realizado(r.tipo_sesion)
        if not tipo_real:
            tipo_real = inferir_tipo_desde_texto(r.comentarios)

        ritmo_real = _calc_ritmo_real(r)

        # Regla 1: misma fecha
        mismos_dia = []
        for p in por_fecha.get(r.fecha, []):
            if p.id in usados_plan:
                continue
            mismos_dia.append(p)

        if mismos_dia:
            filtrados = _filtrar_por_tipo(mismos_dia, tipo_real)
            filtrados = _resolver_por_distancia(filtrados, r.distancia_km)
            filtrados = _resolver_por_ritmo(filtrados, ritmo_real)
            for p in filtrados:
                candidatos.append(("fecha", p, 1.0))

        if not candidatos:
            # Regla 2: fecha +-1 dia y tipo compatible
            for delta in (-1, 1):
                f = r.fecha + timedelta(days=delta)
                for p in por_fecha.get(f, []):
                    if p.id in usados_plan:
                        continue
                    tipos = _tipo_compatible(p.tipo_sesion)
                    if not tipos:
                        continue
                    if tipo_real and tipo_real in tipos:
                        candidatos.append(("fecha_tipo", p, 0.8))

            if candidatos:
                planes = [p for _, p, _ in candidatos]
                filtrados = _filtrar_por_tipo(planes, tipo_real)
                filtrados = _resolver_por_distancia(filtrados, r.distancia_km)
                filtrados = _resolver_por_ritmo(filtrados, ritmo_real)
                candidatos = [("fecha_tipo", p, 0.8) for p in filtrados]

        if len(candidatos) == 1:
            metodo, p, confianza = candidatos[0]
            if persist:
                r.planificado_id = p.id
                r.match_confianza = confianza
                r.match_metodo = metodo
                p.realizado_id = r.id
            usados_plan.add(p.id)

            resumen["vinculados"] += 1
            resumen["detalles"].append(
                {
                    "real_id": r.id,
                    "plan_id": p.id,
                    "fecha_real": r.fecha,
                    "fecha_plan": p.fecha,
                    "metodo": metodo,
                    "confianza": confianza,
                    "tipo": tipo_real,
                }
            )
            continue

        if len(candidatos) > 1:
            resumen["conflictos"] += 1
        else:
            resumen["no_vinculados"] += 1

    if persist:
        session.commit()
    return resumen
