from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from src.ai.coach_actions import resumen_memoria_actions
from src.db.models import CoachAction, PlanAtleta
from src.planning.week_view import obtener_plan_semanal
from src.analysis.plan_vs_real import obtener_resumen_cumplimiento_semanal
from src.planning.load_analysis import analizar_carga_semanal
from src.planning.trend_analysis import analizar_tendencia_semanal
from src.planning.auto_adjust import ajustar_plan_semanal
from src.planning.daily_adjust import ajustar_entrenamientos_diarios


@dataclass
class CoachRecommendation:
    semana: str
    tipo: str  # "semanal" | "diaria"
    resumen: str
    acciones: list[str]
    explicacion: str
    fecha: Any | None = None


class CoachAI:
    """
    CoachAI v1 (explicable):
    - Analiza el plan planificado
    - Detecta riesgo por carga/tendencia
    - Propone ajustes semanales y diarios
    - Devuelve recomendaciones explicadas
    """

    def evaluar_plan(self, session: Session, plan_id: int) -> dict[str, Any]:
        """
        Devuelve un dict con:
        - plan_semanal
        - analisis_carga
        - analisis_tendencia
        """
        plan_semanal = obtener_plan_semanal(session, plan_id)
        carga = analizar_carga_semanal(plan_semanal)
        tendencia = analizar_tendencia_semanal(carga)
        plan = session.get(PlanAtleta, plan_id)
        atleta_id = plan.atleta_id if plan else None
        cumplimiento = (
            obtener_resumen_cumplimiento_semanal(session, plan_id, atleta_id)
            if atleta_id is not None
            else {}
        )

        return {
            "plan_semanal": plan_semanal,
            "carga": carga,
            "tendencia": tendencia,
            "cumplimiento": cumplimiento,
        }
    def proponer_ajustes(self, session: Session, plan_id: int) -> list[CoachRecommendation]:
        evaluacion = self.evaluar_plan(session, plan_id)
        tendencia = evaluacion["tendencia"]
        semanas_ajustadas = self._semanas_ajustadas_recientes(session, plan_id)
        memoria = resumen_memoria_actions(session, plan_id, dias=21)
        cumplimiento = evaluacion.get("cumplimiento", {})

        recomendaciones: list[CoachRecommendation] = []

        # 1) Ajustes semanales
        ajustes_semanales = ajustar_plan_semanal(tendencia)
        # ✅ Fallback v1: si una semana tiene alertas pero no recibió ajuste semanal,
        # generamos un ajuste básico para no dejar semanas peligrosas sin respuesta.
        for semana, data in tendencia.items():
            if not data.get("alertas"):
                continue

            if semana in semanas_ajustadas:
                continue

            if semana not in ajustes_semanales:
                acciones = []

                # Si hay aumento de volumen / progresión rápida → recortar volumen
                if any("aumento" in a.lower() or "progresión" in a.lower() or "subida" in a.lower() for a in data["alertas"]):
                    if memoria["ajustes_por_semana"].get(semana, 0) < 2 and memoria["revertidas_por_semana"].get(semana, 0) == 0:
                        acciones.append("Reducir volumen semanal un 10%")

                # Si hay descarga muy pronunciada → suavizar (no bajar tanto)
                if any("descarga" in a.lower() for a in data["alertas"]):
                    acciones.append("Evitar descarga demasiado pronunciada")

                # Siempre marcar como descarga ligera si hay alertas
                acciones.append("Semana marcada como descarga")

                acciones = _modular_acciones_por_cumplimiento(
                    acciones, cumplimiento.get(semana)
                )
                ajustes_semanales[semana] = {"acciones": acciones}

        for semana, ajuste in ajustes_semanales.items():
            data = tendencia.get(semana, {})
            if not data.get("alertas"):
                continue
            if semana in semanas_ajustadas:
                continue
            if memoria["revertidas_por_semana"].get(semana, 0) > 0:
                acciones = ["Semana marcada como descarga"]
            else:
                acciones = ajuste["acciones"]
            acciones = _modular_acciones_por_cumplimiento(
                acciones, cumplimiento.get(semana)
            )

            explicacion = (
                f"Se proponen ajustes para {semana} porque se detectaron señales de riesgo "
                f"(por ejemplo, subida brusca o exceso de intensidad). "
                f"El objetivo es reducir el riesgo de lesión y mejorar la asimilación."
            )

            recomendaciones.append(
                CoachRecommendation(
                    semana=semana,
                    tipo="semanal",
                    resumen="Ajuste de carga semanal",
                    acciones=acciones,
                    explicacion=explicacion,
                )
            )

        # 2) Ajustes diarios (solo semanas con alertas)
        daily_by_fecha: dict[str, dict] = {}
        for semana, data in tendencia.items():
            if not data["alertas"]:
                continue

            if semana in semanas_ajustadas:
                continue

            entrenamientos = data["entrenamientos"]
            ajustes_diarios = ajustar_entrenamientos_diarios(entrenamientos, data["alertas"])

            for a in ajustes_diarios:
                acciones = a["acciones"]
                fecha = a["fecha"]
                tipo = a["tipo_original"]

                explicacion = (
                    f"En la semana {semana} hay alertas activas ({', '.join(data['alertas'])}). "
                    f"Por ello se ajusta la sesión del {fecha} ({tipo}) para reducir carga/intensidad "
                    f"sin romper la estructura del plan."
                )

                key = fecha.isoformat()
                if key not in daily_by_fecha:
                    daily_by_fecha[key] = {
                        "semana": semana,
                        "fecha": fecha,
                        "acciones": set(),
                        "explicacion": explicacion,
                    }
                for accion in acciones:
                    if memoria["revertidas_recientes"] > 0 and "reducir volumen" in accion.lower():
                        continue
                    if _cumplimiento_bajo(cumplimiento.get(semana)) and "reducir volumen" in accion.lower():
                        continue
                    daily_by_fecha[key]["acciones"].add(accion)

        for item in daily_by_fecha.values():
            recomendaciones.append(
                CoachRecommendation(
                    semana=item["semana"],
                    tipo="diaria",
                    resumen=f"Ajuste de sesión ({item['fecha']})",
                    acciones=sorted(item["acciones"]),
                    explicacion=item["explicacion"],
                    fecha=item["fecha"],
                )
            )

        return recomendaciones

    def _semanas_ajustadas_recientes(self, session: Session, plan_id: int) -> set[str]:
        ahora = datetime.utcnow()
        limite = ahora - timedelta(days=7)
        recs = (
            session.query(CoachAction)
            .filter(CoachAction.plan_id == plan_id)
            .filter(CoachAction.estado == "aplicada")
            .filter(CoachAction.tipo.in_(("semanal", "diaria")))
            .filter(CoachAction.created_at >= limite)
            .all()
        )

        semanas = set()
        for a in recs:
            if a.semana:
                semanas.add(a.semana)
        return semanas


def _cumplimiento_bajo(cumplimiento_semana: dict | None) -> bool:
    if not cumplimiento_semana:
        return False
    return cumplimiento_semana.get("estado") in ("bajo_cumplimiento", "parcial")


def _modular_acciones_por_cumplimiento(
    acciones: list[str], cumplimiento_semana: dict | None
) -> list[str]:
    if not acciones:
        return acciones
    estado = (cumplimiento_semana or {}).get("estado")
    if estado in ("bajo_cumplimiento", "parcial"):
        # Preferir bajar intensidad antes que volumen.
        acciones = [a for a in acciones if "reducir volumen" not in a.lower()]
        if not any("descarga" in a.lower() for a in acciones):
            acciones.append("Semana marcada como descarga")
        # Evitar eliminar sesiones duras si el problema es bajo cumplimiento.
        acciones = [
            a
            for a in acciones
            if not ("eliminar" in a.lower() and "sesión" in a.lower() and "dura" in a.lower())
        ]
        return acciones
    if estado == "exceso":
        # Forzar descarga y reducir sesiones duras.
        if not any("descarga" in a.lower() for a in acciones):
            acciones.append("Semana marcada como descarga")
        if not any("eliminar" in a.lower() and "sesión" in a.lower() and "dura" in a.lower() for a in acciones):
            acciones.append("Eliminar 1 sesión dura")
        if not any("reducir volumen" in a.lower() for a in acciones):
            acciones.append("Reducir volumen semanal un 10%")
    return acciones
