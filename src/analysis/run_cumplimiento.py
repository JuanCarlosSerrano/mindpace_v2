import argparse
from datetime import date

from src.analysis.cumplimiento import calcular_cumplimiento_semanal
from src.db.session import SessionLocal


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _fmt(value) -> str:
    if value is None:
        return "-"
    return str(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=int, required=True)
    parser.add_argument("--atleta", type=int, required=True)
    parser.add_argument("--inicio", default=None)
    parser.add_argument("--fin", default=None)
    parser.add_argument("--format", choices=["text", "csv", "json"], default="text")
    args = parser.parse_args()

    session = SessionLocal()
    data = calcular_cumplimiento_semanal(
        session,
        plan_id=args.plan,
        atleta_id=args.atleta,
        fecha_inicio=_parse_date(args.inicio),
        fecha_fin=_parse_date(args.fin),
    )

    if not data:
        print("✅ No hay datos de cumplimiento.")
        return

    if args.format == "json":
        import json
        print(json.dumps(data, ensure_ascii=True, indent=2))
        return

    if args.format == "csv":
        import csv
        import sys
        writer = csv.writer(sys.stdout)
        writer.writerow(
            [
                "semana",
                "ses_plan",
                "ses_real",
                "ratio_ses",
                "ses_plan_peso",
                "ses_real_peso",
                "exceso_peso",
                "vol_plan",
                "vol_real",
                "ratio_vol",
                "estado",
            ]
        )
        for semana in sorted(data.keys()):
            item = data[semana]
            writer.writerow(
                [
                    semana,
                    item["sesiones_planificadas"],
                    item["sesiones_realizadas"],
                    _fmt(item["ratio_sesiones"]),
                    _fmt(item["sesiones_planificadas_peso"]),
                    _fmt(item["sesiones_realizadas_peso"]),
                    _fmt(item["sesiones_excesivas_peso"]),
                    _fmt(item["volumen_planificado"]),
                    _fmt(item["volumen_real"]),
                    _fmt(item["ratio_volumen"]),
                    item["estado"],
                ]
            )
        return

    headers = [
        "semana",
        "ses_plan",
        "ses_real",
        "ratio_ses",
        "ses_plan_p",
        "ses_real_p",
        "exceso_p",
        "vol_plan",
        "vol_real",
        "ratio_vol",
        "estado",
    ]
    rows = []
    for semana in sorted(data.keys()):
        item = data[semana]
        estado = item["estado"]
        estado_tag = {
            "cumplida": "[OK]",
            "parcial": "[WARN]",
            "bajo_cumplimiento": "[LOW]",
            "exceso": "[HIGH]",
            "no_evaluable": "[NA]",
            "datos_insuficientes": "[NO_DATA]",
        }.get(estado, "[?]")
        rows.append(
            [
                semana,
                item["sesiones_planificadas"],
                item["sesiones_realizadas"],
                _fmt(item["ratio_sesiones"]),
                _fmt(item["sesiones_planificadas_peso"]),
                _fmt(item["sesiones_realizadas_peso"]),
                _fmt(item["sesiones_excesivas_peso"]),
                _fmt(item["volumen_planificado"]),
                _fmt(item["volumen_real"]),
                _fmt(item["ratio_volumen"]),
                f"{estado_tag} {estado}",
            ]
        )

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def _line(sep: str = " | ") -> str:
        parts = []
        for i, h in enumerate(headers):
            parts.append(str(h).ljust(col_widths[i]))
        return sep.join(parts)

    print(_line())
    print("-" * (sum(col_widths) + (3 * (len(headers) - 1))))
    for row in rows:
        parts = []
        for i, cell in enumerate(row):
            parts.append(str(cell).ljust(col_widths[i]))
        print(" | ".join(parts))


if __name__ == "__main__":
    main()
