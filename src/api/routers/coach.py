from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.ai.apply_recommendations import (
    aplicar_ajustes_diarios,
    aplicar_ajustes_semanales,
)
from src.ai.coach import CoachAI
from src.ai.coach_actions import revertir_coach_actions
from src.db.models import CoachAction
from src.ai.coach_actions import registrar_coach_actions
from src.dashboard.weekly_builder import build_weekly_summary
from src.dashboard.weekly_contract import validate_weekly_summary

DB_PATH = os.getenv("DB_PATH", "mindpace_dev.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

router = APIRouter(tags=["coach"])


class ApplyRequest(BaseModel):
    week: str | None = None
    dry_run: bool = False


class RevertRequest(BaseModel):
    week: str | None = None
    ids: list[int] | None = None
    last: int | None = None
    yes: bool = False


def _serialize_recommendation(rec):
    return {
        "action_type": rec.tipo,
        "summary": rec.resumen,
        "actions": rec.acciones,
        "explanation": rec.explicacion,
        "week": rec.semana,
        "date": rec.fecha.isoformat() if rec.fecha else None,
        "scope": rec.scope,
        "reason": rec.reason,
        "confidence": rec.confidence,
        "kind": rec.kind,
        "severity": rec.severity,
        "priority": rec.priority,
    }


@router.post("/plans/{plan_id}/coach/apply")
def post_apply(plan_id: int, payload: ApplyRequest):
    session = Session()
    coach = CoachAI()
    recomendaciones = coach.proponer_ajustes(session, plan_id)
    if payload.week:
        recomendaciones = [r for r in recomendaciones if r.semana == payload.week]

    if payload.dry_run:
        return {
            "dry_run": True,
            "recommendations": [_serialize_recommendation(r) for r in recomendaciones],
        }

    recomendaciones_aplicables = [
        r
        for r in recomendaciones
        if not (
            r.tipo == "semanal"
            and r.resumen == "Datos reales insuficientes"
        )
    ]

    resumen_semanal, acciones_semanales = aplicar_ajustes_semanales(
        session, plan_id, recomendaciones_aplicables
    )
    resumen_diario, acciones_diarias = aplicar_ajustes_diarios(
        session, plan_id, recomendaciones_aplicables
    )

    before_id = (
        session.query(CoachAction.id).order_by(CoachAction.id.desc()).first()
    )
    before_id = before_id[0] if before_id else 0
    registrar_coach_actions(session, acciones_semanales + acciones_diarias)
    new_actions = (
        session.query(CoachAction)
        .filter(CoachAction.id > before_id)
        .order_by(CoachAction.id)
        .all()
    )

    summary = build_weekly_summary(
        plan_id=plan_id, iso_week=payload.week or recomendaciones_aplicables[0].semana
    ) if recomendaciones_aplicables else None
    if summary is not None:
        validate_weekly_summary(summary)

    return {
        "dry_run": False,
        "applied_count": len(acciones_semanales) + len(acciones_diarias),
        "affected_sessions": {
            "weekly": resumen_semanal,
            "daily": resumen_diario,
        },
        "action_ids": [a.id for a in new_actions],
        "weekly_summary": summary,
    }


def _resolve_revert_actions(session, plan_id: int, payload: RevertRequest):
    if payload.ids:
        return (
            session.query(CoachAction)
            .filter(CoachAction.id.in_(payload.ids))
            .filter(CoachAction.estado == "aplicada")
            .filter(CoachAction.tipo.in_(("semanal", "diaria")))
            .order_by(CoachAction.created_at.desc())
            .all()
        )
    if payload.last:
        return (
            session.query(CoachAction)
            .filter(CoachAction.plan_id == plan_id)
            .filter(CoachAction.estado == "aplicada")
            .filter(CoachAction.tipo.in_(("semanal", "diaria")))
            .order_by(CoachAction.created_at.desc())
            .limit(payload.last)
            .all()
        )
    if payload.week:
        return (
            session.query(CoachAction)
            .filter(CoachAction.plan_id == plan_id)
            .filter(CoachAction.semana == payload.week)
            .filter(CoachAction.estado == "aplicada")
            .filter(CoachAction.tipo.in_(("semanal", "diaria")))
            .order_by(CoachAction.created_at.desc())
            .all()
        )
    return []


@router.post("/plans/{plan_id}/coach/revert")
def post_revert(plan_id: int, payload: RevertRequest):
    session = Session()
    acciones = _resolve_revert_actions(session, plan_id, payload)
    if not acciones:
        return {
            "reverted_count": 0,
            "reverted_action_ids": [],
        }

    ids = [a.id for a in acciones]
    resumen = revertir_coach_actions(session, ids, motivo="api")

    summary = None
    if payload.week:
        summary = build_weekly_summary(plan_id=plan_id, iso_week=payload.week)
        validate_weekly_summary(summary)

    return {
        "reverted_count": resumen.get("acciones_revertidas", 0),
        "reverted_action_ids": ids,
        "weekly_summary": summary,
    }
