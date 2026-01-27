from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import asc, desc

from src.db.models import SessionCatalog
from src.db.session import SessionLocal

router = APIRouter(tags=["sessions"])

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class SessionCreateIn(BaseModel):
    name: str
    description: str | None = None
    tipo_sesion: str | None = None
    volumen_base: float | None = None
    intensidad_pct_vam: float | None = None
    formato_series: str | None = None
    recuperacion_seg: int | None = None
    tags: list[str] | None = None
    blocks: list[dict] | None = None


class SessionUpdateIn(BaseModel):
    name: str | None = None
    description: str | None = None
    tipo_sesion: str | None = None
    volumen_base: float | None = None
    intensidad_pct_vam: float | None = None
    formato_series: str | None = None
    recuperacion_seg: int | None = None
    tags: list[str] | None = None
    blocks: list[dict] | None = None


def _serialize_session(item: SessionCatalog) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "tipo_sesion": item.tipo_sesion,
        "volumen_base": float(item.volumen_base or 0) if item.volumen_base is not None else None,
        "intensidad_pct_vam": float(item.intensidad_pct_vam or 0) if item.intensidad_pct_vam is not None else None,
        "formato_series": item.formato_series,
        "recuperacion_seg": item.recuperacion_seg,
        "tags": item.tags_json or [],
        "blocks": item.blocks_json or [],
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _apply_tag_filter(items: list[SessionCatalog], tags: list[str]) -> list[SessionCatalog]:
    if not tags:
        return items
    filtered = []
    tags_lower = [t.lower() for t in tags]
    for t in items:
        item_tags = [x.lower() for x in (t.tags_json or [])]
        if all(tag in item_tags for tag in tags_lower):
            filtered.append(t)
    return filtered


@router.get("/sessions")
def list_sessions(
    q: str | None = Query(None),
    tipo: str | None = Query(None),
    tag: list[str] | None = Query(None),
    sort: str = Query("updated", pattern="^(updated|name|load)$"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
):
    session = SessionLocal()
    try:
        query = session.query(SessionCatalog)
        if q:
            like = f"%{q.lower()}%"
            query = query.filter(
                (SessionCatalog.name.ilike(like))
                | (SessionCatalog.description.ilike(like))
            )
        if tipo:
            query = query.filter(SessionCatalog.tipo_sesion == tipo)

        order_by = {
            "updated": desc(SessionCatalog.updated_at),
            "name": asc(SessionCatalog.name),
            "load": desc(SessionCatalog.volumen_base),
        }[sort]

        items = query.order_by(order_by).all()
        items = _apply_tag_filter(items, tag or [])
        total = len(items)
        items = items[offset: offset + limit]
        return {"items": [_serialize_session(i) for i in items], "total": total}
    finally:
        session.close()


@router.get("/sessions/{session_id}")
def get_session_detail(session_id: int):
    session = SessionLocal()
    try:
        item = session.get(SessionCatalog, session_id)
        if item is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
        return _serialize_session(item)
    finally:
        session.close()


@router.post("/sessions")
def create_session(payload: SessionCreateIn):
    session = SessionLocal()
    try:
        item = SessionCatalog(
            name=payload.name,
            description=payload.description,
            tipo_sesion=payload.tipo_sesion,
            volumen_base=payload.volumen_base,
            intensidad_pct_vam=payload.intensidad_pct_vam,
            formato_series=payload.formato_series,
            recuperacion_seg=payload.recuperacion_seg,
            tags_json=payload.tags or [],
            blocks_json=payload.blocks or [],
            updated_at=datetime.now(timezone.utc),
        )
        session.add(item)
        session.commit()
        return {"id": item.id}
    finally:
        session.close()


@router.put("/sessions/{session_id}")
def update_session(session_id: int, payload: SessionUpdateIn):
    session = SessionLocal()
    try:
        item = session.get(SessionCatalog, session_id)
        if item is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(status_code=400, detail={"error": "NO_FIELDS"})
        if "name" in data:
            item.name = data["name"]
        if "description" in data:
            item.description = data["description"]
        if "tipo_sesion" in data:
            item.tipo_sesion = data["tipo_sesion"]
        if "volumen_base" in data:
            item.volumen_base = data["volumen_base"]
        if "intensidad_pct_vam" in data:
            item.intensidad_pct_vam = data["intensidad_pct_vam"]
        if "formato_series" in data:
            item.formato_series = data["formato_series"]
        if "recuperacion_seg" in data:
            item.recuperacion_seg = data["recuperacion_seg"]
        if "tags" in data:
            item.tags_json = data["tags"]
        if "blocks" in data:
            item.blocks_json = data["blocks"]
        item.updated_at = datetime.now(timezone.utc)
        session.commit()
        return {"id": item.id}
    finally:
        session.close()


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int):
    session = SessionLocal()
    try:
        item = session.get(SessionCatalog, session_id)
        if item is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
        session.delete(item)
        session.commit()
        return {"deleted": True}
    finally:
        session.close()
