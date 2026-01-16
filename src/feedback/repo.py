from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from src.db.models import AthleteFeedback, EntrenamientoPlanificado


def _now():
    return datetime.now(timezone.utc)


def _validate_range(name: str, value: int | None, min_val: int, max_val: int) -> None:
    if value is None:
        return
    if not isinstance(value, int):
        raise ValueError(f"{name} debe ser int")
    if value < min_val or value > max_val:
        raise ValueError(f"{name} fuera de rango ({min_val}-{max_val})")


def upsert_feedback(
    session: Session,
    athlete_id: int,
    plan_id: int | None,
    session_date: date,
    payload: dict,
) -> AthleteFeedback:
    _validate_range("rpe", payload.get("rpe"), 1, 10)
    _validate_range("mood", payload.get("mood"), 1, 5)
    _validate_range("fatigue", payload.get("fatigue"), 1, 10)
    _validate_range("soreness", payload.get("soreness"), 1, 10)

    feedback = (
        session.query(AthleteFeedback)
        .filter(AthleteFeedback.athlete_id == athlete_id)
        .filter(AthleteFeedback.session_date == session_date)
        .first()
    )
    now = _now()
    if feedback is None:
        feedback = AthleteFeedback(
            athlete_id=athlete_id,
            plan_id=plan_id,
            session_date=session_date,
            created_at=now,
            updated_at=now,
        )
        session.add(feedback)
    else:
        feedback.updated_at = now
        if plan_id is not None:
            feedback.plan_id = plan_id

    for key in ("rpe", "mood", "fatigue", "soreness", "pain_flag", "notes"):
        if key in payload:
            setattr(feedback, key, payload.get(key))

    session.commit()
    return feedback


def get_feedback_range(
    session: Session,
    athlete_id: int,
    start_date: date,
    end_date: date,
) -> list[AthleteFeedback]:
    return (
        session.query(AthleteFeedback)
        .filter(AthleteFeedback.athlete_id == athlete_id)
        .filter(AthleteFeedback.session_date >= start_date)
        .filter(AthleteFeedback.session_date <= end_date)
        .order_by(AthleteFeedback.session_date)
        .all()
    )


def summarize_feedback_week(
    session: Session,
    athlete_id: int,
    start_date: date,
    end_date: date,
    plan_id: int | None = None,
) -> dict:
    feedbacks = get_feedback_range(session, athlete_id, start_date, end_date)
    count = len(feedbacks)

    rpe_values = [f.rpe for f in feedbacks if f.rpe is not None]
    avg_rpe = round(sum(rpe_values) / len(rpe_values), 2) if rpe_values else None

    high_fatigue_days = sum(1 for f in feedbacks if (f.fatigue or 0) >= 8)
    pain_days = sum(1 for f in feedbacks if f.pain_flag)
    pain_signal = pain_days > 0

    notes_preview = []
    for f in feedbacks:
        if f.notes:
            notes_preview.append(
                {
                    "date": f.session_date.isoformat(),
                    "text": f.notes[:120],
                }
            )
        if len(notes_preview) >= 3:
            break

    planned_days = None
    if plan_id is not None:
        planned = (
            session.query(EntrenamientoPlanificado)
            .filter(EntrenamientoPlanificado.plan_id == plan_id)
            .filter(EntrenamientoPlanificado.fecha >= start_date)
            .filter(EntrenamientoPlanificado.fecha <= end_date)
            .all()
        )
        planned_days = len({p.fecha for p in planned})

    if planned_days:
        coverage = round(count / planned_days, 2)
    else:
        coverage = 0.0

    return {
        "count": count,
        "coverage": coverage,
        "avg_rpe": avg_rpe,
        "high_fatigue_days": high_fatigue_days,
        "pain_days": pain_days,
        "pain_signal": pain_signal,
        "notes_preview": notes_preview,
    }
