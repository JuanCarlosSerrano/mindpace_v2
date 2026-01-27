from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timezone, timedelta
import io

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.ai.coach import CoachAI
from src.analysis.cumplimiento import calcular_cumplimiento_semanal
from src.db.models import CoachAction, EntrenamientoRealizado, PlanAtleta
from src.feedback.repo import summarize_feedback_week
from src.planning.load_analysis import analizar_carga_semanal
from src.planning.trend_analysis import analizar_tendencia_semanal
from src.planning.week_view import obtener_plan_semanal
from src.db.models import ComparacionPlanReal

DB_PATH = os.getenv("DB_PATH", "mindpace_dev.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def _week_key_tuple(week_key: str) -> tuple[int, int]:
    parts = week_key.split("-W")
    if len(parts) != 2:
        raise ValueError(f"Semana invalida: {week_key}")
    return int(parts[0]), int(parts[1])


def _week_range(week_key: str) -> tuple[date, date]:
    year, week = _week_key_tuple(week_key)
    start = date.fromisocalendar(year, week, 1)
    end = start + timedelta(days=6)
    return start, end


def _cumplimiento_status(estado: str | None) -> dict[str, str]:
    estado = estado or "no_evaluable"
    mapping = {
        "cumplida": ("OK", "cumplida"),
        "parcial": ("PARTIAL", "parcial"),
        "bajo_cumplimiento": ("LOW", "bajo_cumplimiento"),
        "exceso": ("HIGH", "exceso"),
        "datos_insuficientes": ("NO_DATA", "datos_insuficientes"),
        "no_evaluable": ("NA", "no_evaluable"),
    }
    status, label = mapping.get(estado, ("NA", estado))
    return {"status": status, "label": label}


def _acciones_para_semana(
    acciones: list[CoachAction], week_key: str
) -> list[CoachAction]:
    start, end = _week_range(week_key)
    seleccionadas = []
    for a in acciones:
        if a.semana == week_key:
            seleccionadas.append(a)
            continue
        if a.fecha and start <= a.fecha <= end:
            seleccionadas.append(a)
            continue
        if a.created_at and start <= a.created_at.date() <= end:
            seleccionadas.append(a)
            continue
    return seleccionadas


def _acciones_desde_action(action: CoachAction) -> list[str]:
    raw = action.acciones
    if isinstance(raw, list):
        return [str(a) for a in raw]
    if isinstance(raw, dict):
        if isinstance(raw.get("acciones"), list):
            return [str(a) for a in raw["acciones"]]
        acciones = []
        for value in raw.values():
            if isinstance(value, list):
                acciones.extend([str(a) for a in value])
            elif isinstance(value, str):
                acciones.append(value)
        return acciones
    if isinstance(raw, str):
        return [raw]
    return []

def _action_code(message: str) -> str:
    lower = message.lower()
    if "semana marcada como descarga" in lower:
        return "WEEK_DELOAD"
    if "reducir volumen semanal" in lower:
        return "WEEK_REDUCE_VOLUME"
    if "eliminar" in lower and "sesión" in lower and "dura" in lower:
        return "WEEK_REMOVE_HARD_SESSION"
    if "reducir intensidad" in lower:
        return "SESSION_REDUCE_INTENSITY"
    if "evitar descarga" in lower:
        return "WEEK_AVOID_TOO_DELOAD"
    if "importar entrenamientos reales" in lower:
        return "INFO_IMPORT_REAL"
    return "ACTION_GENERIC"


def _actions_payload(messages: list[str]) -> list[dict]:
    payload = []
    for msg in messages:
        payload.append({"code": _action_code(msg), "message": msg})
    return payload


def build_weekly_summary(
    plan_id: int,
    iso_week: str,
    session: Session | None = None,
) -> dict:
    session_local = session or SessionLocal()
    start_date, end_date = _week_range(iso_week)
    plan = session_local.get(PlanAtleta, plan_id)
    atleta_id = plan.atleta_id if plan else None

    plan_semanal = obtener_plan_semanal(session_local, plan_id)
    buffer = io.StringIO()
    with redirect_stdout(buffer), redirect_stderr(buffer):
        carga = analizar_carga_semanal(plan_semanal)
    tendencia = analizar_tendencia_semanal(carga)
    cumplimiento = (
        calcular_cumplimiento_semanal(session_local, plan_id, atleta_id)
        if atleta_id is not None
        else {}
    )
    cumplimiento_item = cumplimiento.get(iso_week, {})
    status_info = _cumplimiento_status(cumplimiento_item.get("estado"))

    reales = (
        session_local.query(EntrenamientoRealizado)
        .filter(EntrenamientoRealizado.atleta_id == atleta_id)
        .filter(EntrenamientoRealizado.fecha >= start_date)
        .filter(EntrenamientoRealizado.fecha <= end_date)
        .all()
        if atleta_id is not None
        else []
    )

    comparaciones = (
        session_local.query(ComparacionPlanReal)
        .filter(ComparacionPlanReal.plan_id == plan_id)
        .filter(ComparacionPlanReal.atleta_id == atleta_id)
        .filter(ComparacionPlanReal.fecha >= start_date)
        .filter(ComparacionPlanReal.fecha <= end_date)
        .all()
        if atleta_id is not None
        else []
    )

    acciones_all = (
        session_local.query(CoachAction)
        .filter(CoachAction.plan_id == plan_id)
        .order_by(CoachAction.created_at)
        .all()
    )
    acciones_semana = _acciones_para_semana(acciones_all, iso_week)
    acciones_aplicadas = [
        {
            "id": a.id,
            "action_type": a.tipo,
            "state": a.estado,
            "actions": _actions_payload(_acciones_desde_action(a)),
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in acciones_semana
    ]

    coach = CoachAI()
    recomendaciones = [
        r
        for r in coach.proponer_ajustes(session_local, plan_id)
        if r.semana == iso_week
    ]
    coach_recommended = [
        {
            "action_type": r.tipo,
            "summary": r.resumen,
            "actions": _actions_payload(r.acciones),
            "explanation": r.explicacion,
            "date": r.fecha.isoformat() if r.fecha else None,
            "scope": r.scope,
            "reason": r.reason,
            "confidence": r.confidence,
            "kind": r.kind,
            "severity": r.severity,
            "priority": r.priority,
        }
        for r in recomendaciones
    ]

    plan_item = plan_semanal.get(iso_week, {})
    tendencia_item = tendencia.get(iso_week, {})

    sesiones_plan = plan_item.get("sesiones", 0)
    sesiones_real = cumplimiento_item.get("sesiones_realizadas", 0)
    cobertura = (
        round(sesiones_real / sesiones_plan, 2) if sesiones_plan else None
    )

    plan_detail = []
    for e in plan_item.get("entrenamientos", []):
        plan_detail.append(
            {
                "id": e.id,
                "date": e.fecha.isoformat(),
                "tipo_sesion": e.tipo_sesion,
                "volumen_objetivo": float(e.volumen_objetivo or 0)
                if e.volumen_objetivo is not None
                else None,
                "ritmo_objetivo": e.ritmo_objetivo,
                "detalle_series": e.detalle_series,
                "blocks": e.blocks_json or [],
            }
        )

    summary = {
        "meta": {
            "plan_id": plan_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_confidence_ratio": cobertura,
        },
        "week": {
            "iso": iso_week,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "plan": {
            "sessions_count": sesiones_plan,
            "volume_km_total": plan_item.get("volumen_total", 0.0),
            "by_type": {
                k: int(v) for k, v in plan_item.get("por_tipo", {}).items()
            },
            "sessions_detail": plan_detail,
        },
        "real": {
            "sessions_count": len(reales),
            "volume_km_total": float(
                cumplimiento_item.get("volumen_real", 0.0) or 0.0
            ),
            "coverage_ratio": cobertura,
        },
        "comparison": {
            "linked_sessions_count": len(comparaciones),
        },
        "compliance": {
            "status": status_info["status"],
            "label": status_info["label"],
            "ratio_volume": cumplimiento_item.get("ratio_volumen"),
            "ratio_sessions": cumplimiento_item.get("ratio_sesiones"),
        },
        "load": {
            "load_index": tendencia_item.get("indice_carga"),
            "trend": tendencia_item.get("tendencia"),
            "alerts": tendencia_item.get("alertas", []),
        },
        "alerts": {
            "plan": tendencia_item.get("alertas", []),
            "real_risk": [],
        },
        "coach": {
            "recommended": coach_recommended,
            "recommended_count": len(coach_recommended),
            "remaining_after_apply_count": max(
                0, len(coach_recommended) - len(acciones_aplicadas)
            ),
        },
        "actions": {
            "applied": acciones_aplicadas,
            "applied_count": len(acciones_aplicadas),
            "reverted_count": 0,
        },
        "history": acciones_aplicadas,
        "history_count": len(acciones_aplicadas),
        "feedback": summarize_feedback_week(
            session_local,
            atleta_id,
            start_date,
            end_date,
            plan_id=plan_id,
        )
        if atleta_id is not None
        else {
            "count": 0,
            "coverage": 0.0,
            "avg_rpe": None,
            "high_fatigue_days": 0,
            "pain_days": 0,
            "pain_signal": False,
            "notes_preview": [],
        },
    }

    if session is None:
        session_local.close()
    return summary
