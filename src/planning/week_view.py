from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from src.db.models import EntrenamientoPlanificado


def obtener_plan_semanal(session: Session, plan_id: int):
    """
    Devuelve el plan agrupado por semanas ISO.
    """
    entrenamientos = (
        session.query(EntrenamientoPlanificado)
        .filter(EntrenamientoPlanificado.plan_id == plan_id)
        .order_by(EntrenamientoPlanificado.fecha)
        .all()
    )

    semanas = defaultdict(lambda: {
        "sesiones": 0,
        "volumen_total": 0.0,
        "por_tipo": defaultdict(int),
        "entrenamientos": []
    })

    for e in entrenamientos:
        iso_year, iso_week, _ = e.fecha.isocalendar()
        clave = f"{iso_year}-W{iso_week:02d}"

        semanas[clave]["sesiones"] += 1
        semanas[clave]["volumen_total"] += float(e.volumen_objetivo or 0)
        semanas[clave]["por_tipo"][e.tipo_sesion] += 1
        semanas[clave]["entrenamientos"].append(e)

    return dict(semanas)
