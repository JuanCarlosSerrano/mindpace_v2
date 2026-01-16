from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from src.ai.coach_actions import resumen_memoria_actions
from src.db.models import CoachAction, PlanAtleta
from src.planning.week_view import obtener_plan_semanal
from src.analysis.cumplimiento import calcular_cumplimiento_semanal
from src.planning.load_analysis import analizar_carga_semanal
from src.planning.trend_analysis import analizar_tendencia_semanal
from src.planning.auto_adjust import ajustar_plan_semanal
from src.planning.daily_adjust import ajustar_entrenamientos_diarios
from src.feedback.repo import summarize_feedback_week

MIN_SESIONES_REALES_PARA_AJUSTES = 3
MIN_RATIO_SESIONES_PARA_AJUSTES = Decimal("0.50")


@dataclass
class CoachRecommendation:
    semana: str
    tipo: str  # "semanal" | "diaria"
    resumen: str
    acciones: list[str]
    explicacion: str
    fecha: Any | None = None
    scope: str | None = None
    reason: str | None = None
    confidence: str | None = None
    kind: str | None = None
    severity: str | None = None
    priority: int | None = None


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
            calcular_cumplimiento_semanal(session, plan_id, atleta_id)
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
        plan_semanal = evaluacion["plan_semanal"]
        semanas_ajustadas = self._semanas_ajustadas_recientes(session, plan_id)
        memoria = resumen_memoria_actions(session, plan_id, dias=21)
        cumplimiento = evaluacion.get("cumplimiento", {})
        feedback = self._feedback_por_semana(
            session, plan_id, plan_semanal, tendencia
        )

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
            no_data = _cumplimiento_no_data(cumplimiento.get(semana))
            cobertura_ok = _cobertura_suficiente(cumplimiento.get(semana))
            if not no_data and not cobertura_ok and not _alertas_fuertes(data.get("alertas", [])):
                recomendaciones.append(
                    CoachRecommendation(
                        semana=semana,
                        tipo="semanal",
                        resumen="Cobertura insuficiente",
                        acciones=[
                            "Importar entrenamientos reales para evaluar cumplimiento"
                        ],
                        explicacion=(
                            f"Semana {semana} con datos reales insuficientes para activar ajustes "
                            "automáticos. Se requiere mayor cobertura de sesiones."
                        ),
                        scope="weekly",
                        reason="NO_DATA",
                        confidence="low",
                        kind="info",
                    )
                )
                continue
            if memoria["revertidas_por_semana"].get(semana, 0) > 0:
                acciones = ["Semana marcada como descarga"]
            else:
                acciones = ajuste["acciones"]
            acciones = _modular_acciones_por_cumplimiento(
                acciones, cumplimiento.get(semana)
            )
            if no_data:
                acciones = _filtrar_acciones_no_data(acciones)
                if not acciones:
                    acciones = ["Importar entrenamientos reales para evaluar cumplimiento"]

            reason = _reason_from_cumplimiento(cumplimiento.get(semana))
            explicacion = (
                f"Se proponen ajustes para {semana} porque se detectaron señales de riesgo "
                f"(por ejemplo, subida brusca o exceso de intensidad). "
                f"El objetivo es reducir el riesgo de lesión y mejorar la asimilación."
            )
            if no_data:
                explicacion += " NO_DATA: modo conservador por falta de datos reales."

            recomendaciones.append(
                CoachRecommendation(
                    semana=semana,
                    tipo="semanal",
                    resumen="Ajuste de carga semanal",
                    acciones=acciones,
                    explicacion=explicacion,
                    scope="weekly",
                    reason=reason,
                    kind="adjustment",
                )
            )

        # Recomendacion informativa si NO_DATA y sin alertas.
        for semana, data in tendencia.items():
            if data.get("alertas"):
                continue
            if not _cumplimiento_no_data(cumplimiento.get(semana)):
                continue
            recomendaciones.append(
                CoachRecommendation(
                    semana=semana,
                    tipo="semanal",
                    resumen="Datos reales insuficientes",
                    acciones=["Importar entrenamientos reales para evaluar cumplimiento"],
                    explicacion=(
                        f"Semana {semana} sin datos reales importados. "
                        "NO_DATA: se sugiere importar entrenamientos para evaluar cumplimiento."
                    ),
                    scope="weekly",
                    reason="NO_DATA",
                    confidence="low",
                    kind="info",
                )
            )

        # 2) Ajustes diarios (solo semanas con alertas)
        daily_by_fecha: dict[str, dict] = {}
        for semana, data in tendencia.items():
            if not data["alertas"]:
                continue

            if semana in semanas_ajustadas:
                continue
            if (
                not _cumplimiento_no_data(cumplimiento.get(semana))
                and not _cobertura_suficiente(cumplimiento.get(semana))
                and not _alertas_fuertes(data.get("alertas", []))
            ):
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
                    if _cumplimiento_no_data(cumplimiento.get(semana)):
                        if "reducir intensidad" not in accion.lower():
                            continue
                    daily_by_fecha[key]["acciones"].add(accion)

        for item in daily_by_fecha.values():
            if not item["acciones"]:
                continue
            reason = _reason_from_cumplimiento(cumplimiento.get(item["semana"]))
            recomendaciones.append(
                CoachRecommendation(
                    semana=item["semana"],
                    tipo="diaria",
                    resumen=f"Ajuste de sesión ({item['fecha']})",
                    acciones=sorted(item["acciones"]),
                    explicacion=item["explicacion"],
                    fecha=item["fecha"],
                    scope="daily",
                    reason=reason,
                    kind="adjustment",
                )
            )

        weekly_summary_by_week = {}
        for semana in set(tendencia.keys()) | set(plan_semanal.keys()):
            weekly_summary_by_week[semana] = {
                "week": {"iso": semana},
                "feedback": feedback.get(
                    semana,
                    {
                        "count": 0,
                        "coverage": 0.0,
                        "avg_rpe": None,
                        "high_fatigue_days": 0,
                        "pain_days": 0,
                        "pain_signal": False,
                        "notes_preview": [],
                    },
                ),
                "compliance": {
                    "status": _map_compliance_status(
                        (cumplimiento.get(semana) or {}).get("estado")
                    )
                },
                "plan_entrenamientos": plan_semanal.get(semana, {}).get(
                    "entrenamientos", []
                ),
                "tendencia": tendencia.get(semana, {}),
            }

        recomendaciones = apply_feedback_modulation(recomendaciones, weekly_summary_by_week)
        return classify_recommendations(recomendaciones)

    def _semanas_ajustadas_recientes(self, session: Session, plan_id: int) -> set[str]:
        ahora = datetime.now(timezone.utc)
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

    def _feedback_por_semana(self, session: Session, plan_id: int, plan_semanal: dict, tendencia: dict) -> dict:
        plan = session.get(PlanAtleta, plan_id)
        atleta_id = plan.atleta_id if plan else None
        if atleta_id is None:
            return {}
        semanas = set(plan_semanal.keys()) | set(tendencia.keys())
        feedback_por_semana = {}
        for semana in semanas:
            start_date, end_date = _week_range(semana)
            feedback_por_semana[semana] = summarize_feedback_week(
                session,
                atleta_id,
                start_date,
                end_date,
                plan_id=plan_id,
            )
        return feedback_por_semana


def _cumplimiento_bajo(cumplimiento_semana: dict | None) -> bool:
    if not cumplimiento_semana:
        return False
    return cumplimiento_semana.get("estado") in ("bajo_cumplimiento", "parcial")


def _cumplimiento_no_data(cumplimiento_semana: dict | None) -> bool:
    if not cumplimiento_semana:
        return False
    return cumplimiento_semana.get("estado") == "datos_insuficientes"

def _cobertura_suficiente(cumplimiento_semana: dict | None) -> bool:
    if not cumplimiento_semana:
        return False
    if cumplimiento_semana.get("estado") in ("datos_insuficientes", "no_evaluable"):
        return False
    sesiones_plan = cumplimiento_semana.get("sesiones_planificadas") or 0
    sesiones_real = cumplimiento_semana.get("sesiones_realizadas") or 0
    ratio_sesiones = cumplimiento_semana.get("ratio_sesiones")
    if sesiones_plan <= 0:
        return False
    minimo_real = min(MIN_SESIONES_REALES_PARA_AJUSTES, sesiones_plan)
    if sesiones_real < minimo_real:
        return False
    if ratio_sesiones is None:
        return False
    try:
        ratio_valor = Decimal(str(ratio_sesiones))
    except Exception:
        return False
    return ratio_valor >= MIN_RATIO_SESIONES_PARA_AJUSTES


def _alertas_fuertes(alertas: list[str]) -> bool:
    return any(a.strip().startswith("🚨") for a in alertas)


def _map_compliance_status(estado: str | None) -> str:
    if estado == "cumplida":
        return "OK"
    if estado in ("bajo_cumplimiento", "parcial"):
        return "LOW"
    if estado == "datos_insuficientes":
        return "NO_DATA"
    if estado == "exceso":
        return "HIGH"
    return "NA"


def _reason_from_cumplimiento(cumplimiento_semana: dict | None) -> str | None:
    if not cumplimiento_semana:
        return None
    estado = cumplimiento_semana.get("estado")
    if estado in ("bajo_cumplimiento", "parcial"):
        return "LOW"
    if estado == "datos_insuficientes":
        return "NO_DATA"
    if estado == "cumplida":
        return "OK"
    return None


def _feedback_negativo(feedback: dict) -> bool:
    avg_rpe = feedback.get("avg_rpe") or 0
    high_fatigue = feedback.get("high_fatigue_days") or 0
    return avg_rpe >= 8 or high_fatigue >= 2


def _feedback_pain(feedback: dict) -> bool:
    pain_days = feedback.get("pain_days") or 0
    return pain_days >= 1


def _week_range(week_key: str) -> tuple[date, date]:
    year, week = week_key.split("-W")
    start = date.fromisocalendar(int(year), int(week), 1)
    end = start + timedelta(days=6)
    return start, end


def apply_feedback_modulation(
    recommendations: list[CoachRecommendation],
    weekly_summary: dict,
) -> list[CoachRecommendation]:
    recs_by_week: dict[str, list[CoachRecommendation]] = {}
    for r in recommendations:
        recs_by_week.setdefault(r.semana, []).append(r)

    result: list[CoachRecommendation] = []

    for semana, summary in weekly_summary.items():
        week_recs = recs_by_week.get(semana, [])
        feedback = summary.get("feedback", {})
        compliance = summary.get("compliance", {})
        status = compliance.get("status")
        plan_entrenos = summary.get("plan_entrenamientos", [])

        feedback_neg = _feedback_negativo(feedback)
        pain = _feedback_pain(feedback)

        def _add_info(summary_text: str, reason: str, confidence: str, explicacion: str):
            result.append(
                CoachRecommendation(
                    semana=semana,
                    tipo="semanal",
                    resumen=summary_text,
                    acciones=["Revisión manual del plan recomendada"]
                    if "Dolor reportado" in summary_text
                    else ["Importar entrenamientos reales para evaluar cumplimiento"],
                    explicacion=explicacion,
                    scope="weekly",
                    reason=reason,
                    confidence=confidence,
                    kind="info",
                )
            )

        if pain:
            _add_info(
                "Dolor reportado por el atleta; se recomienda revisión manual del plan",
                "PAIN_FLAG",
                "high",
                "Feedback indica dolor (pain_flag). Se bloquean ajustes automáticos.",
            )
            continue

        if status == "NO_DATA" and feedback.get("count", 0) >= 1:
            _add_info(
                "Feedback del atleta indica fatiga/esfuerzo alto; importar entrenamientos reales para evaluar",
                "NO_DATA",
                "medium",
                "NO_DATA con feedback presente. Se sugiere importar entrenamientos reales para evaluar.",
            )
            continue

        if status == "OK" and feedback_neg:
            filtered_week_recs: list[CoachRecommendation] = []
            for r in week_recs:
                if r.tipo == "semanal":
                    acciones = [a for a in r.acciones if "descarga" not in a.lower()]
                    if not acciones:
                        continue
                    r.acciones = acciones
                filtered_week_recs.append(r)

            for r in filtered_week_recs:
                result.append(r)

            for e in plan_entrenos:
                fecha = getattr(e, "fecha", None)
                if fecha is None:
                    continue
                if any(
                    rec.tipo == "diaria" and rec.fecha == fecha for rec in filtered_week_recs
                ):
                    continue
                explicacion = (
                    "Cumplimiento OK con feedback negativo "
                    f"(avg_rpe={feedback.get('avg_rpe')}, "
                    f"high_fatigue_days={feedback.get('high_fatigue_days')}). "
                    "Se reduce intensidad por precaucion."
                )
                result.append(
                    CoachRecommendation(
                        semana=semana,
                        tipo="diaria",
                        resumen="Reducir intensidad por esfuerzo percibido alto",
                        acciones=["Reducir intensidad (ritmo más conservador)"],
                        explicacion=explicacion,
                        fecha=fecha,
                        scope="daily",
                        reason="FEEDBACK",
                        confidence="medium",
                        kind="adjustment",
                    )
                )
            continue

        if status == "LOW" and feedback_neg:
            for r in week_recs:
                if "feedback" not in r.resumen.lower():
                    r.resumen = f"{r.resumen} + feedback alto"
                r.explicacion = (
                    f"{r.explicacion} Feedback alto (avg_rpe={feedback.get('avg_rpe')}, "
                    f"high_fatigue_days={feedback.get('high_fatigue_days')})."
                )
                r.reason = "LOW + FEEDBACK"
                r.confidence = "medium"
                result.append(r)
            continue

        for r in week_recs:
            result.append(r)

    return result


def classify_recommendations(
    recommendations: list[CoachRecommendation],
) -> list[CoachRecommendation]:
    for rec in recommendations:
        reason = (rec.reason or "").upper()
        kind = (rec.kind or "").lower()

        if reason == "PAIN_FLAG":
            rec.severity = "high"
            rec.priority = 1
            continue

        if "FEEDBACK" in reason:
            rec.severity = "medium"
            rec.priority = 2
            continue

        if reason == "LOW":
            rec.severity = "medium"
            rec.priority = 3
            continue

        if reason == "NO_DATA":
            rec.severity = "info"
            rec.priority = 4
            continue

        if kind == "info":
            rec.severity = "info"
            rec.priority = 5
            continue

        rec.severity = rec.severity or "low"
        rec.priority = rec.priority or 5

    return sorted(recommendations, key=lambda r: (r.priority or 5, r.semana, r.tipo))


def _filtrar_acciones_no_data(acciones: list[str]) -> list[str]:
    permitidas = []
    for a in acciones:
        lower = a.lower()
        if "reducir volumen" in lower:
            continue
        if "eliminar" in lower and "sesión" in lower and "dura" in lower:
            continue
        permitidas.append(a)
    return permitidas


def _modular_acciones_por_cumplimiento(
    acciones: list[str], cumplimiento_semana: dict | None
) -> list[str]:
    if not acciones:
        return acciones
    estado = (cumplimiento_semana or {}).get("estado")
    if estado in ("datos_insuficientes", "no_evaluable"):
        # No castigar cuando falta informacion: evitar reducciones fuertes.
        return _filtrar_acciones_no_data(acciones)
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
