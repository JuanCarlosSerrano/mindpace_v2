from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable

from sqlalchemy.orm import Session

from src.db.models import CoachAction, EntrenamientoPlanificado


def registrar_coach_actions(session: Session, acciones: Iterable[dict]) -> None:
    for a in acciones:
        session.add(
            CoachAction(
                plan_id=a["plan_id"],
                semana=a.get("semana"),
                fecha=a.get("fecha"),
                tipo=a["tipo"],
                acciones=a["acciones"],
                estado=a.get("estado", "aplicada"),
            )
        )
    session.commit()


def listar_coach_actions(
    session: Session, plan_id: int | None = None, limit: int | None = None
) -> list[CoachAction]:
    q = session.query(CoachAction)
    if plan_id is not None:
        q = q.filter(CoachAction.plan_id == plan_id)
    q = q.order_by(CoachAction.created_at.desc())
    if limit is not None:
        q = q.limit(limit)
    return list(q.all())


def obtener_action_ids_por_semana(
    session: Session, plan_id: int, semana: str
) -> list[int]:
    acciones = (
        session.query(CoachAction)
        .filter(CoachAction.plan_id == plan_id)
        .filter(CoachAction.semana == semana)
        .filter(CoachAction.estado == "aplicada")
        .order_by(CoachAction.created_at.desc())
        .all()
    )
    return [a.id for a in acciones]


def revertir_coach_actions(
    session: Session, action_ids: list[int], motivo: str | None = None
) -> dict:
    acciones = (
        session.query(CoachAction)
        .filter(CoachAction.id.in_(action_ids))
        .order_by(CoachAction.created_at.desc())
        .all()
    )

    resumen = {
        "acciones_revertidas": 0,
        "sesiones_actualizadas": 0,
        "sesiones_restauradas": 0,
    }

    acciones_por_plan: dict[int, list[CoachAction]] = {}
    for action in acciones:
        if action.estado != "aplicada":
            continue
        acciones_por_plan.setdefault(action.plan_id, []).append(action)

        payload = action.acciones or {}
        cambios = payload.get("cambios", [])
        for c in reversed(cambios):
            before = c.get("before")
            if not before:
                continue

            entrenamiento_id = c.get("entrenamiento_id")
            entreno = session.get(EntrenamientoPlanificado, entrenamiento_id)
            if c.get("deleted"):
                if entreno is None:
                    entreno = EntrenamientoPlanificado(id=entrenamiento_id)
                    session.add(entreno)
                    resumen["sesiones_restauradas"] += 1
                else:
                    resumen["sesiones_actualizadas"] += 1

                _apply_snapshot(entreno, before)
                continue

            if entreno is None:
                entreno = EntrenamientoPlanificado(id=entrenamiento_id)
                session.add(entreno)
                resumen["sesiones_restauradas"] += 1
            else:
                resumen["sesiones_actualizadas"] += 1

            _apply_snapshot(entreno, before)

        action.estado = "revertida"
        resumen["acciones_revertidas"] += 1

    for plan_id, items in acciones_por_plan.items():
        semanas = {a.semana for a in items if a.semana}
        semana = semanas.pop() if len(semanas) == 1 else None
        session.add(
            CoachAction(
                plan_id=plan_id,
                semana=semana,
                fecha=None,
                tipo="reversion",
                acciones={
                    "revierte": [a.id for a in items],
                    "motivo": motivo,
                },
                estado="aplicada",
            )
        )

    session.commit()
    return resumen


def revertir_semana(session: Session, plan_id: int, semana: str) -> dict:
    action_ids = obtener_action_ids_por_semana(session, plan_id, semana)
    if not action_ids:
        return {
            "acciones_revertidas": 0,
            "sesiones_actualizadas": 0,
            "sesiones_restauradas": 0,
        }
    return revertir_coach_actions(session, action_ids)


def resumen_memoria_actions(
    session: Session, plan_id: int, dias: int = 21
) -> dict:
    ahora = datetime.utcnow()
    limite = ahora - timedelta(days=dias)
    acciones = (
        session.query(CoachAction)
        .filter(CoachAction.plan_id == plan_id)
        .filter(CoachAction.created_at >= limite)
        .filter(CoachAction.tipo.in_(("semanal", "diaria")))
        .all()
    )

    ajustes_por_semana: dict[str, int] = {}
    revertidas_por_semana: dict[str, int] = {}
    total_revertidas = 0

    for a in acciones:
        if a.semana:
            ajustes_por_semana[a.semana] = ajustes_por_semana.get(a.semana, 0) + 1
            if a.estado == "revertida":
                revertidas_por_semana[a.semana] = (
                    revertidas_por_semana.get(a.semana, 0) + 1
                )
        if a.estado == "revertida":
            total_revertidas += 1

    return {
        "ajustes_por_semana": ajustes_por_semana,
        "revertidas_por_semana": revertidas_por_semana,
        "revertidas_recientes": total_revertidas,
    }


def _apply_snapshot(entreno: EntrenamientoPlanificado, snapshot: dict) -> None:
    entreno.plan_id = snapshot.get("plan_id")
    entreno.fecha = date.fromisoformat(snapshot.get("fecha"))
    entreno.tipo_sesion = snapshot.get("tipo_sesion")

    vol = snapshot.get("volumen_objetivo")
    entreno.volumen_objetivo = Decimal(str(vol)) if vol is not None else None

    entreno.ritmo_objetivo = snapshot.get("ritmo_objetivo")
    entreno.detalle_series = snapshot.get("detalle_series")
    entreno.comentarios_entrenador = snapshot.get("comentarios_entrenador")
