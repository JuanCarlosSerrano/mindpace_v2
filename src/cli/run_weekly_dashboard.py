from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

from src.analysis.cumplimiento import calcular_cumplimiento_semanal
from src.db.models import CoachAction, PlanAtleta
from src.db.session import SessionLocal
from src.planning.load_analysis import analizar_carga_semanal
from src.planning.trend_analysis import analizar_tendencia_semanal
from src.planning.week_view import obtener_plan_semanal


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


def _fmt(value) -> str:
    if value is None:
        return "-"
    return str(value)


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


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for v in values:
        if v in seen:
            continue
        seen.add(v)
        result.append(v)
    return result


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


def build_weekly_dashboard_rows(
    session,
    plan_id: int,
    inicio: str | None = None,
    fin: str | None = None,
) -> list[dict]:
    plan = session.get(PlanAtleta, plan_id)
    atleta_id = plan.atleta_id if plan else None

    plan_semanal = obtener_plan_semanal(session, plan_id)
    if not plan_semanal:
        return []

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        carga = analizar_carga_semanal(plan_semanal)
    tendencia = analizar_tendencia_semanal(carga)

    cumplimiento = (
        calcular_cumplimiento_semanal(session, plan_id, atleta_id)
        if atleta_id is not None
        else {}
    )

    acciones_all = (
        session.query(CoachAction)
        .filter(CoachAction.plan_id == plan_id)
        .order_by(CoachAction.created_at)
        .all()
    )

    weeks = sorted(plan_semanal.keys(), key=_week_key_tuple)
    if inicio:
        weeks = [w for w in weeks if _week_key_tuple(w) >= _week_key_tuple(inicio)]
    if fin:
        weeks = [w for w in weeks if _week_key_tuple(w) <= _week_key_tuple(fin)]

    rows = []
    for semana in weeks:
        plan_item = plan_semanal.get(semana, {})
        cumplimiento_item = cumplimiento.get(semana, {})
        tendencia_item = tendencia.get(semana, {})

        sesiones_plan = plan_item.get("sesiones", 0)
        volumen_plan = plan_item.get("volumen_total", 0.0)
        sesiones_real = cumplimiento_item.get("sesiones_realizadas", 0)
        volumen_real = cumplimiento_item.get("volumen_real", 0.0)
        ratio_ses = cumplimiento_item.get("ratio_sesiones")
        ratio_vol = cumplimiento_item.get("ratio_volumen")
        estado = cumplimiento_item.get("estado", "no_evaluable")
        cobertura = (
            round(sesiones_real / sesiones_plan, 2)
            if sesiones_plan
            else None
        )

        alertas = tendencia_item.get("alertas", [])
        alertas_resumen = "; ".join(alertas[:2])
        if len(alertas) > 2:
            alertas_resumen = f"{alertas_resumen} +{len(alertas) - 2}"
        if not alertas_resumen:
            alertas_resumen = "-"

        acciones_semana = _acciones_para_semana(acciones_all, semana)
        acciones_count = len(acciones_semana)
        tipo_counts = {}
        acciones_flat = []
        for a in acciones_semana:
            tipo_counts[a.tipo] = tipo_counts.get(a.tipo, 0) + 1
            acciones_flat.extend(_acciones_desde_action(a))
        acciones_flat = _unique(acciones_flat)
        acciones_top = acciones_flat[:2]
        tipos_resumen = ", ".join(f"{k}:{v}" for k, v in sorted(tipo_counts.items()))

        rows.append(
            {
                "semana": semana,
                "sesiones_plan": sesiones_plan,
                "volumen_plan": round(volumen_plan, 2),
                "sesiones_real": sesiones_real,
                "volumen_real": round(float(volumen_real or 0), 2),
                "estado_cumplimiento": estado,
                "ratio_vol": ratio_vol,
                "ratio_ses": ratio_ses,
                "cobertura_datos": cobertura,
                "indice_carga": tendencia_item.get("indice_carga"),
                "alertas": alertas,
                "alertas_resumen": alertas_resumen,
                "acciones_count": acciones_count,
                "acciones_tipos": tipos_resumen or "-",
                "acciones_top": acciones_top,
            }
        )
    return rows


def _render_text(rows: list[dict], verbose: bool) -> str:
    headers = [
        "semana",
        "ses_plan",
        "vol_plan",
        "ses_real",
        "vol_real",
        "ratio_ses",
        "ratio_vol",
        "cobertura",
        "estado",
        "carga",
        "alertas",
        "acciones",
    ]

    table_rows = []
    for item in rows:
        acciones_txt = f"{item['acciones_count']} ({item['acciones_tipos']})"
        table_rows.append(
            [
                item["semana"],
                item["sesiones_plan"],
                _fmt(item["volumen_plan"]),
                item["sesiones_real"],
                _fmt(item["volumen_real"]),
                _fmt(item["ratio_ses"]),
                _fmt(item["ratio_vol"]),
                _fmt(item["cobertura_datos"]),
                item["estado_cumplimiento"],
                _fmt(item["indice_carga"]),
                item["alertas_resumen"],
                acciones_txt,
            ]
        )

    col_widths = [len(h) for h in headers]
    for row in table_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def _line(row) -> str:
        parts = []
        for i, cell in enumerate(row):
            parts.append(str(cell).ljust(col_widths[i]))
        return " | ".join(parts)

    output = []
    output.append(_line(headers))
    output.append("-" * (sum(col_widths) + (3 * (len(headers) - 1))))
    for row in table_rows:
        output.append(_line(row))

    if verbose:
        for item in rows:
            output.append("")
            output.append(f"Semana {item['semana']}")
            output.append(f"  Alertas: {', '.join(item['alertas']) or '-'}")
            output.append(
                f"  Acciones top: {', '.join(item['acciones_top']) or '-'}"
            )

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=int, required=True)
    parser.add_argument("--inicio", default=None)
    parser.add_argument("--fin", default=None)
    parser.add_argument("--format", choices=["text", "csv", "json"], default="text")
    parser.add_argument("--output", default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    session = SessionLocal()
    rows = build_weekly_dashboard_rows(
        session, plan_id=args.plan, inicio=args.inicio, fin=args.fin
    )

    if not rows:
        content = "✅ No hay datos semanales."
    elif args.format == "json":
        content = json.dumps(rows, ensure_ascii=True, indent=2)
    elif args.format == "csv":
        import csv
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            row = dict(row)
            row["alertas"] = ", ".join(row["alertas"])
            row["acciones_top"] = ", ".join(row["acciones_top"])
            writer.writerow(row)
        content = buffer.getvalue()
    else:
        content = _render_text(rows, verbose=args.verbose)

    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        print(content)


if __name__ == "__main__":
    main()
