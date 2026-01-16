import re
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request

from src.dashboard.serializers import serialize_week_text
from src.dashboard.weekly_builder import build_weekly_summary
from src.dashboard.weekly_contract import validate_weekly_summary

router = APIRouter(tags=["dashboard"])

_ISO_WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")


def _validate_iso_week(iso_week: str) -> None:
    if not _ISO_WEEK_RE.match(iso_week):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_ISO_WEEK",
                "message": "Semana inválida",
                "week": iso_week,
            },
        )
    year_str, week_str = iso_week.split("-W")
    year = int(year_str)
    week = int(week_str)
    last_week = date(year, 12, 28).isocalendar()[1]
    if week < 1 or week > last_week:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_ISO_WEEK",
                "message": "Semana inválida",
                "week": iso_week,
                "max_week": last_week,
            },
        )


@router.get("/plans/{plan_id}/weeks/{iso_week}")
def get_weekly_dashboard(
    plan_id: int,
    iso_week: str,
    request: Request,
    format: str = Query("json", pattern="^(json|text)$"),
    validate: bool = Query(True),
    include_sessions_detail: bool = Query(False),
):
    if not getattr(request.app.state, "db_ready", True):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DB_NOT_INITIALIZED",
                "message": "Base de datos sin inicializar",
                "details": [getattr(request.app.state, "db_error", "")],
            },
        )
    _validate_iso_week(iso_week)

    try:
        summary = build_weekly_summary(plan_id=plan_id, iso_week=iso_week)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_ISO_WEEK",
                "message": "Semana inválida",
                "week": iso_week,
                "details": [str(exc)],
            },
        )

    if (
        summary.get("plan", {}).get("sessions_count", 0) == 0
        and summary.get("real", {}).get("sessions_count", 0) == 0
        and summary.get("feedback", {}).get("count", 0) == 0
    ):
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NO_DATA_FOR_WEEK",
                "plan_id": plan_id,
                "week": iso_week,
            },
        )
    if validate:
        try:
            validate_weekly_summary(summary)
        except ValueError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "WEEKLY_CONTRACT_INVALID",
                    "details": [line for line in str(exc).splitlines() if line.strip()],
                    "plan_id": plan_id,
                    "week": iso_week,
                },
            )

    if format == "text":
        return {"text": serialize_week_text(summary)}

    return summary
