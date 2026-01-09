from __future__ import annotations

from typing import Iterable
import unicodedata

from sqlalchemy.orm import Session

from src.db.models import EntrenamientoRealizado


def inferir_tipo_desde_texto(texto: str | None) -> str | None:
    if not texto:
        return None

    norm = unicodedata.normalize("NFKD", texto)
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    t = norm.lower()

    if "rodaje" in t or "easy" in t:
        return "rodaje"
    if "series" in t or "intervalos" in t:
        return "series"
    if "tempo" in t:
        return "tempo"
    if "umbral" in t or "threshold" in t:
        return "umbral"
    return None


def backfill_tipo_sesion(
    session: Session,
    atleta_id: int | None = None,
    dry_run: bool = False,
) -> dict:
    q = session.query(EntrenamientoRealizado).filter(
        EntrenamientoRealizado.tipo_sesion.is_(None)
    )
    if atleta_id is not None:
        q = q.filter(EntrenamientoRealizado.atleta_id == atleta_id)

    actualizados = 0
    sin_match = 0
    for r in q.all():
        texto = getattr(r, "comentario", None) or r.comentarios or ""
        tipo = inferir_tipo_desde_texto(texto)
        if not tipo:
            sin_match += 1
            continue
        actualizados += 1
        if not dry_run:
            r.tipo_sesion = tipo

    if not dry_run:
        session.commit()

    return {"actualizados": actualizados, "sin_match": sin_match}
