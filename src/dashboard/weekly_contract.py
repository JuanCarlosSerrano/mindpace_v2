from __future__ import annotations

from decimal import Decimal
from typing import Any


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float, Decimal))


def _require_dict(value: Any, path: str, errors: list[str]) -> dict | None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return None
    return value


def _require_list(value: Any, path: str, errors: list[str]) -> list | None:
    if not isinstance(value, list):
        errors.append(f"{path}: expected array")
        return None
    return value


def _require_str(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{path}: expected string")


def _require_int(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, int):
        errors.append(f"{path}: expected int")


def _require_bool(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, bool):
        errors.append(f"{path}: expected bool")


def _require_number_or_none(value: Any, path: str, errors: list[str]) -> None:
    if value is None:
        return
    if not _is_number(value):
        errors.append(f"{path}: expected number or null")


def _get_any(data: dict, keys: list[str]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _validate_actions_list(value: Any, path: str, errors: list[str]) -> None:
    items = _require_list(value, path, errors)
    if items is None:
        return
    for idx, item in enumerate(items):
        item_path = f"{path}[{idx}]"
        if isinstance(item, str):
            continue
        if isinstance(item, dict):
            if "message" in item:
                _require_str(item["message"], f"{item_path}.message", errors)
            if "code" in item:
                _require_str(item["code"], f"{item_path}.code", errors)
            if "message" not in item and "code" not in item:
                errors.append(f"{item_path}: expected action object with code/message")
            continue
        errors.append(f"{item_path}: expected string or action object")


def _validate_action_entry(action: dict, path: str, errors: list[str]) -> None:
    action_type = _get_any(action, ["action_type", "tipo"])
    state = _get_any(action, ["state", "estado"])
    actions_field = _get_any(action, ["actions", "acciones"])

    if "id" in action:
        _require_int(action["id"], f"{path}.id", errors)
    else:
        errors.append(f"{path}.id: required")

    if action_type is None:
        errors.append(f"{path}.action_type: required")
    else:
        _require_str(action_type, f"{path}.action_type", errors)

    if state is None:
        errors.append(f"{path}.state: required")
    else:
        _require_str(state, f"{path}.state", errors)

    if actions_field is None:
        errors.append(f"{path}.actions: required")
    else:
        _validate_actions_list(actions_field, f"{path}.actions", errors)

    if "created_at" in action and action["created_at"] is not None:
        _require_str(action["created_at"], f"{path}.created_at", errors)


def validate_weekly_summary(summary: dict) -> None:
    """
    Validates WeeklySummary JSON contract. Raises ValueError if invalid.
    Compatible with current output and legacy field names.
    """
    errors: list[str] = []
    root = _require_dict(summary, "$", errors)
    if root is None:
        raise ValueError("\n".join(errors))

    meta = _require_dict(root.get("meta"), "$.meta", errors)
    if meta is not None:
        if "plan_id" in meta:
            _require_int(meta["plan_id"], "$.meta.plan_id", errors)
        else:
            errors.append("$.meta.plan_id: required")
        if "generated_at" in meta:
            _require_str(meta["generated_at"], "$.meta.generated_at", errors)
        else:
            errors.append("$.meta.generated_at: required")
        confidence = _get_any(meta, ["data_confidence_ratio", "data_confidence"])
        _require_number_or_none(confidence, "$.meta.data_confidence", errors)

    week = _require_dict(root.get("week"), "$.week", errors)
    if week is not None:
        for key in ("iso", "start_date", "end_date"):
            if key in week:
                _require_str(week[key], f"$.week.{key}", errors)
            else:
                errors.append(f"$.week.{key}: required")

    plan = _require_dict(root.get("plan"), "$.plan", errors)
    if plan is not None:
        sessions = _get_any(plan, ["sessions_count", "sesiones"])
        volume = _get_any(plan, ["volume_km_total", "volumen_km"])
        by_type = _get_any(plan, ["by_type", "por_tipo"])
        if sessions is None:
            errors.append("$.plan.sessions_count: required")
        else:
            _require_int(sessions, "$.plan.sessions_count", errors)
        if volume is None:
            errors.append("$.plan.volume_km_total: required")
        else:
            _require_number_or_none(volume, "$.plan.volume_km_total", errors)
        if by_type is None:
            errors.append("$.plan.by_type: required")
        else:
            by_type_obj = _require_dict(by_type, "$.plan.by_type", errors)
            if by_type_obj is not None:
                for k, v in by_type_obj.items():
                    if not isinstance(k, str) or not isinstance(v, int):
                        errors.append("$.plan.by_type: expected string keys and int values")
                        break
        if "sessions_detail" in plan:
            _require_list(plan["sessions_detail"], "$.plan.sessions_detail", errors)

    real = _require_dict(root.get("real"), "$.real", errors)
    if real is not None:
        sessions = _get_any(real, ["sessions_count", "sesiones"])
        volume = _get_any(real, ["volume_km_total", "volumen_km"])
        coverage = _get_any(real, ["coverage_ratio", "cobertura"])
        if sessions is None:
            errors.append("$.real.sessions_count: required")
        else:
            _require_int(sessions, "$.real.sessions_count", errors)
        if volume is None:
            errors.append("$.real.volume_km_total: required")
        else:
            _require_number_or_none(volume, "$.real.volume_km_total", errors)
        _require_number_or_none(coverage, "$.real.coverage_ratio", errors)

    comparison = _require_dict(root.get("comparison"), "$.comparison", errors)
    if comparison is not None:
        linked = _get_any(comparison, ["linked_sessions_count", "sesiones_vinculadas"])
        if linked is None:
            errors.append("$.comparison.linked_sessions_count: required")
        else:
            _require_int(linked, "$.comparison.linked_sessions_count", errors)

    compliance = _require_dict(root.get("compliance"), "$.compliance", errors)
    if compliance is not None:
        status = compliance.get("status")
        label = compliance.get("label")
        if status is None:
            errors.append("$.compliance.status: required")
        else:
            _require_str(status, "$.compliance.status", errors)
        if label is None:
            errors.append("$.compliance.label: required")
        else:
            _require_str(label, "$.compliance.label", errors)
        ratio_vol = _get_any(compliance, ["ratio_volume", "ratio_vol"])
        ratio_ses = _get_any(compliance, ["ratio_sessions", "ratio_ses"])
        _require_number_or_none(ratio_vol, "$.compliance.ratio_volume", errors)
        _require_number_or_none(ratio_ses, "$.compliance.ratio_sessions", errors)

    load = _require_dict(root.get("load"), "$.load", errors)
    if load is not None:
        load_index = _get_any(load, ["load_index", "indice_carga"])
        trend = _get_any(load, ["trend", "tendencia"])
        alerts = load.get("alerts", [])
        _require_number_or_none(load_index, "$.load.load_index", errors)
        if trend is not None:
            _require_str(trend, "$.load.trend", errors)
        _require_list(alerts, "$.load.alerts", errors)

    alerts = _require_dict(root.get("alerts"), "$.alerts", errors)
    if alerts is not None:
        _require_list(alerts.get("plan", []), "$.alerts.plan", errors)
        _require_list(alerts.get("real_risk", []), "$.alerts.real_risk", errors)

    coach = _require_dict(root.get("coach"), "$.coach", errors)
    if coach is not None:
        recs = coach.get("recommended", [])
        _require_list(recs, "$.coach.recommended", errors)
        remaining = _get_any(coach, ["remaining_after_apply_count", "remaining_after_apply"])
        if remaining is None:
            errors.append("$.coach.remaining_after_apply: required")
        else:
            _require_int(remaining, "$.coach.remaining_after_apply", errors)

    actions = _require_dict(root.get("actions"), "$.actions", errors)
    if actions is not None:
        applied = actions.get("applied", [])
        applied_list = _require_list(applied, "$.actions.applied", errors)
        if applied_list is not None:
            for idx, action in enumerate(applied_list):
                if not isinstance(action, dict):
                    errors.append(f"$.actions.applied[{idx}]: expected object")
                    continue
                _validate_action_entry(action, f"$.actions.applied[{idx}]", errors)
        reverted = _get_any(actions, ["reverted_count", "reverted"])
        _require_number_or_none(reverted, "$.actions.reverted", errors)

    history = _require_list(root.get("history", []), "$.history", errors)
    if history is not None:
        for idx, action in enumerate(history):
            if not isinstance(action, dict):
                errors.append(f"$.history[{idx}]: expected object")
                continue
            _validate_action_entry(action, f"$.history[{idx}]", errors)

    feedback = _require_dict(root.get("feedback"), "$.feedback", errors)
    if feedback is not None:
        for key in ("count", "high_fatigue_days", "pain_days"):
            if key in feedback:
                _require_int(feedback[key], f"$.feedback.{key}", errors)
            else:
                errors.append(f"$.feedback.{key}: required")
        if "coverage" in feedback:
            _require_number_or_none(feedback["coverage"], "$.feedback.coverage", errors)
        else:
            errors.append("$.feedback.coverage: required")
        if "avg_rpe" in feedback:
            _require_number_or_none(feedback["avg_rpe"], "$.feedback.avg_rpe", errors)
        else:
            errors.append("$.feedback.avg_rpe: required")
        if "pain_signal" in feedback:
            _require_bool(feedback["pain_signal"], "$.feedback.pain_signal", errors)
        else:
            errors.append("$.feedback.pain_signal: required")
        notes = _require_list(
            feedback.get("notes_preview", []), "$.feedback.notes_preview", errors
        )
        if notes is not None:
            for idx, note in enumerate(notes):
                if not isinstance(note, dict):
                    errors.append(f"$.feedback.notes_preview[{idx}]: expected object")
                    continue
                if "date" in note:
                    _require_str(note["date"], f"$.feedback.notes_preview[{idx}].date", errors)
                else:
                    errors.append(f"$.feedback.notes_preview[{idx}].date: required")
                if "text" in note:
                    _require_str(note["text"], f"$.feedback.notes_preview[{idx}].text", errors)
                else:
                    errors.append(f"$.feedback.notes_preview[{idx}].text: required")

    if errors:
        raise ValueError("\n".join(errors))
