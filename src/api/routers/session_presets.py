from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import asc, desc

from src.db.models import SessionPreset
from src.db.session import SessionLocal

router = APIRouter(tags=["session_presets"])

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class PresetCreateIn(BaseModel):
    entrenador_id: int
    label: str = Field(..., min_length=1)
    tipo_sesion: str | None = None
    volumen_base: float | None = None
    intensidad_pct_vam: float | None = None
    formato_series: str | None = None
    recuperacion_seg: int | None = None
    tags: list[str] | None = None


class PresetUpdateIn(BaseModel):
    label: str | None = None
    tipo_sesion: str | None = None
    volumen_base: float | None = None
    intensidad_pct_vam: float | None = None
    formato_series: str | None = None
    recuperacion_seg: int | None = None
    tags: list[str] | None = None


def _serialize_preset(item: SessionPreset) -> dict:
    return {
        "id": item.id,
        "entrenador_id": item.entrenador_id,
        "label": item.label,
        "tipo_sesion": item.tipo_sesion,
        "volumen_base": float(item.volumen_base or 0) if item.volumen_base is not None else None,
        "intensidad_pct_vam": float(item.intensidad_pct_vam or 0)
        if item.intensidad_pct_vam is not None
        else None,
        "formato_series": item.formato_series,
        "recuperacion_seg": item.recuperacion_seg,
        "tags": item.tags_json or [],
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@router.get("/session-presets")
def list_presets(
    entrenador_id: int = Query(..., ge=1),
    sort: str = Query("updated", pattern="^(updated|label)$"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
):
    session = SessionLocal()
    try:
        query = session.query(SessionPreset).filter(
            SessionPreset.entrenador_id == entrenador_id
        )
        order_by = {
            "updated": desc(SessionPreset.updated_at),
            "label": asc(SessionPreset.label),
        }[sort]
        items = query.order_by(order_by).all()
        total = len(items)
        items = items[offset: offset + limit]
        return {"items": [_serialize_preset(i) for i in items], "total": total}
    finally:
        session.close()


@router.post("/session-presets")
def create_preset(payload: PresetCreateIn):
    session = SessionLocal()
    try:
        item = SessionPreset(
            entrenador_id=payload.entrenador_id,
            label=payload.label,
            tipo_sesion=payload.tipo_sesion,
            volumen_base=payload.volumen_base,
            intensidad_pct_vam=payload.intensidad_pct_vam,
            formato_series=payload.formato_series,
            recuperacion_seg=payload.recuperacion_seg,
            tags_json=payload.tags or [],
            updated_at=datetime.now(timezone.utc),
        )
        session.add(item)
        session.commit()
        return {"id": item.id}
    finally:
        session.close()


@router.put("/session-presets/{preset_id}")
def update_preset(
    preset_id: int,
    payload: PresetUpdateIn,
    entrenador_id: int | None = Query(None, ge=1),
):
    session = SessionLocal()
    try:
        item = session.get(SessionPreset, preset_id)
        if item is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
        if entrenador_id is not None and item.entrenador_id != entrenador_id:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(status_code=400, detail={"error": "NO_FIELDS"})
        if "label" in data:
            item.label = data["label"]
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
        item.updated_at = datetime.now(timezone.utc)

        session.commit()
        return {"id": item.id}
    finally:
        session.close()


@router.delete("/session-presets/{preset_id}")
def delete_preset(
    preset_id: int,
    entrenador_id: int | None = Query(None, ge=1),
):
    session = SessionLocal()
    try:
        item = session.get(SessionPreset, preset_id)
        if item is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
        if entrenador_id is not None and item.entrenador_id != entrenador_id:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
        session.delete(item)
        session.commit()
        return {"deleted": True}
    finally:
        session.close()
