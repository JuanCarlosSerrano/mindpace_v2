from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from sqlalchemy import asc, desc

from src.db.models import TemplateCatalog, PlantillaPlan, PlantillaSesion
from src.db.session import SessionLocal
from src.planning.engine import generar_plan_desde_plantilla

router = APIRouter(tags=["templates"])

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class TemplateSessionIn(BaseModel):
    week: int = Field(..., ge=1)
    day_of_week: int = Field(..., ge=1, le=7)
    tipo_sesion: str | None = None
    volumen_base: float | None = None
    intensidad_pct_vam: float | None = None
    formato_series: str | None = None
    recuperacion_seg: int | None = None
    blocks: list[dict] | None = None


class TemplateCreateIn(BaseModel):
    name: str
    description: str | None = None
    goal: str | None = None
    level: str | None = None
    duration_weeks: int | None = Field(None, ge=1)
    tags: list[str] | None = None
    estimated_weekly_load: float | None = None
    sessions: list[TemplateSessionIn]


class TemplateGenerateIn(BaseModel):
    athlete_id: int
    start_date: str
    objetivo_descripcion: str | None = ""


def _build_weekly_preview(template: TemplateCatalog) -> list[dict]:
    weeks = int(template.duration_weeks or 0)
    base_load = Decimal(str(template.estimated_weekly_load or 0))
    if weeks <= 0 or base_load <= 0:
        return []

    preview = []
    for i in range(1, weeks + 1):
        factor = Decimal("1.00")
        if weeks >= 6:
            if i == weeks:
                factor = Decimal("0.60")
            elif i == weeks - 1:
                factor = Decimal("0.80")
            else:
                factor = Decimal("0.90") + Decimal("0.02") * Decimal(i - 1)
                if factor > Decimal("1.10"):
                    factor = Decimal("1.10")
        else:
            if i == weeks:
                factor = Decimal("0.80")
            else:
                factor = Decimal("0.90") + Decimal("0.03") * Decimal(i - 1)
        load = (base_load * factor).quantize(Decimal("0.1"))
        preview.append(
            {
                "week": i,
                "load": float(load),
                "focus_tags": (template.tags_json or [])[:2],
            }
        )
    return preview


def _serialize_template(template: TemplateCatalog) -> dict:
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "goal": template.goal,
        "level": template.level,
        "duration_weeks": template.duration_weeks,
        "tags": template.tags_json or [],
        "estimated_weekly_load": float(template.estimated_weekly_load or 0),
        "source_key": template.source_key,
        "updated_at": (
            template.updated_at.isoformat()
            if isinstance(template.updated_at, datetime)
            else None
        ),
    }


def _apply_tag_filter(items: list[TemplateCatalog], tags: list[str]) -> list[TemplateCatalog]:
    if not tags:
        return items
    filtered = []
    tags_lower = [t.lower() for t in tags]
    for t in items:
        item_tags = [x.lower() for x in (t.tags_json or [])]
        if all(tag in item_tags for tag in tags_lower):
            filtered.append(t)
    return filtered


@router.get("/templates")
def list_templates(
    q: str | None = Query(None),
    goal: str | None = Query(None),
    level: str | None = Query(None),
    min_weeks: int | None = Query(None, ge=1),
    max_weeks: int | None = Query(None, ge=1),
    tag: list[str] | None = Query(None),
    sort: str = Query("updated", pattern="^(updated|load|duration|name)$"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
):
    session = SessionLocal()
    try:
        query = session.query(TemplateCatalog)

        if q:
            like = f"%{q.lower()}%"
            query = query.filter(
                (TemplateCatalog.name.ilike(like))
                | (TemplateCatalog.description.ilike(like))
            )
        if goal:
            query = query.filter(TemplateCatalog.goal == goal)
        if level:
            query = query.filter(TemplateCatalog.level == level)
        if min_weeks is not None:
            query = query.filter(TemplateCatalog.duration_weeks >= min_weeks)
        if max_weeks is not None:
            query = query.filter(TemplateCatalog.duration_weeks <= max_weeks)

        order_by = {
            "updated": desc(TemplateCatalog.updated_at),
            "load": desc(TemplateCatalog.estimated_weekly_load),
            "duration": desc(TemplateCatalog.duration_weeks),
            "name": asc(TemplateCatalog.name),
        }[sort]

        items = query.order_by(order_by).all()
        items = _apply_tag_filter(items, tag or [])
        total = len(items)
        items = items[offset: offset + limit]
        return {
            "items": [_serialize_template(t) for t in items],
            "total": total,
        }
    finally:
        session.close()


@router.get("/templates/meta")
def get_templates_meta():
    session = SessionLocal()
    try:
        items = session.query(TemplateCatalog).all()
        goals = sorted({t.goal for t in items if t.goal})
        levels = sorted({t.level for t in items if t.level})
        tags = sorted({tag for t in items for tag in (t.tags_json or [])})
        return {"goals": goals, "levels": levels, "tags": tags}
    finally:
        session.close()


@router.get("/templates/{template_id}")
def get_template_detail(template_id: int):
    session = SessionLocal()
    try:
        template = session.get(TemplateCatalog, template_id)
        if template is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
        data = _serialize_template(template)
        data["weekly_preview"] = _build_weekly_preview(template)
        return data
    finally:
        session.close()


@router.post("/templates")
def create_template(payload: TemplateCreateIn):
    session = SessionLocal()
    try:
        duration_weeks = payload.duration_weeks or _infer_duration_weeks(payload.sessions)
        if duration_weeks is None:
            raise HTTPException(status_code=400, detail={"error": "MISSING_DURATION"})
        estimated_load = (
            payload.estimated_weekly_load
            if payload.estimated_weekly_load is not None
            else _estimate_weekly_load(payload.sessions)
        )

        plantilla = PlantillaPlan(
            nombre=payload.name,
            descripcion=payload.description,
            distancia_objetivo=payload.goal,
            nivel=payload.level,
            duracion_semanas=duration_weeks,
            metodo="editor",
        )
        session.add(plantilla)
        session.flush()

        for s in payload.sessions:
            session.add(
                PlantillaSesion(
                    plantilla_id=plantilla.id,
                    semana=s.week,
                    dia_semana=s.day_of_week,
                    tipo_sesion=s.tipo_sesion,
                    volumen_base=s.volumen_base,
                    intensidad_pct_vam=s.intensidad_pct_vam,
                    formato_series=s.formato_series,
                    recuperacion_seg=s.recuperacion_seg,
                    blocks_json=s.blocks or [],
                )
            )

        session.add(
            TemplateCatalog(
                name=payload.name,
                description=payload.description,
                goal=payload.goal,
                level=payload.level,
                duration_weeks=duration_weeks,
                tags_json=payload.tags or [],
                estimated_weekly_load=estimated_load,
                source_key=f"plantilla:{plantilla.id}",
                updated_at=datetime.now(timezone.utc),
            )
        )
        session.commit()
        return {"id": plantilla.id, "catalog_name": payload.name}
    finally:
        session.close()


@router.post("/templates/{template_id}/generate")
def generate_plan_from_template(template_id: int, payload: TemplateGenerateIn):
    session = SessionLocal()
    try:
        try:
            fecha_inicio = datetime.fromisoformat(payload.start_date).date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_DATE", "field": "start_date"},
            )
        plan_id = generar_plan_desde_plantilla(
            session=session,
            atleta_id=payload.athlete_id,
            plantilla_id=template_id,
            fecha_inicio=fecha_inicio,
            objetivo_descripcion=payload.objetivo_descripcion or "",
        )
        return {"plan_id": plan_id}
    finally:
        session.close()


def _infer_duration_weeks(sessions: list[TemplateSessionIn]) -> int | None:
    if not sessions:
        return None
    return max(s.week for s in sessions)


def _estimate_weekly_load(sessions: list[TemplateSessionIn]) -> float | None:
    if not sessions:
        return None
    by_week: dict[int, Decimal] = {}
    for s in sessions:
        if s.volumen_base is None:
            continue
        by_week.setdefault(s.week, Decimal("0"))
        by_week[s.week] += Decimal(str(s.volumen_base))
    if not by_week:
        return None
    avg = sum(by_week.values()) / Decimal(str(len(by_week)))
    return float(avg.quantize(Decimal("0.1")))
