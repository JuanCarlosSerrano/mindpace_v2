from __future__ import annotations

from decimal import Decimal


def _jsonify(value):
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonify(v) for v in value]
    if isinstance(value, Decimal):
        return float(value)
    return value


def serialize_week_json(summary: dict) -> dict:
    return _jsonify(summary)


def serialize_week_text(summary: dict) -> str:
    lines = []
    week = summary["week"]["iso"]
    lines.append(f"Semana {week}")
    lines.append("-" * 40)

    compliance = summary["compliance"]
    lines.append(
        f"Estado: [{compliance['status']}] {compliance['label']}"
    )

    load = summary.get("load", {})
    alerts = load.get("alerts", [])
    if alerts:
        lines.append("Alertas:")
        for a in alerts:
            lines.append(f" - {a}")
    else:
        lines.append("Alertas: -")

    acciones = summary.get("actions", {}).get("applied_count", 0)
    lines.append(f"Acciones aplicadas: {acciones}")
    return "\n".join(lines)
