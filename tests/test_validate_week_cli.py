from src.dashboard import validate_week


def test_validate_week_cli_ok(monkeypatch):
    summary = {
        "meta": {
            "plan_id": 2,
            "generated_at": "2026-01-10T09:11:52.499386+00:00",
            "data_confidence": 0.5,
        },
        "week": {
            "iso": "2026-W03",
            "start_date": "2026-01-12",
            "end_date": "2026-01-18",
        },
        "plan": {"sesiones": 1, "volumen_km": 10.0, "por_tipo": {"rodaje": 1}},
        "real": {"sesiones": 1, "volumen_km": 10.0, "cobertura": 1.0},
        "comparison": {"sesiones_vinculadas": 1},
        "compliance": {
            "status": "OK",
            "label": "cumplida",
            "ratio_vol": 1.0,
            "ratio_ses": 1.0,
        },
        "load": {"indice_carga": 10.0, "tendencia": "➖ estable", "alerts": []},
        "alerts": {"plan": [], "real_risk": []},
        "coach": {"recommended": [], "remaining_after_apply": 0},
        "actions": {"applied": [], "reverted": 0},
        "history": [],
        "feedback": {
            "count": 0,
            "coverage": 0.0,
            "avg_rpe": None,
            "high_fatigue_days": 0,
            "pain_days": 0,
            "pain_signal": False,
            "notes_preview": [],
        },
    }
    monkeypatch.setattr(validate_week, "build_weekly_summary", lambda **_: summary)
    ok, errors, _ = validate_week.run_validate(2, "2026-W03")
    assert ok
    assert errors == []


def test_validate_week_cli_invalid(monkeypatch):
    summary = {
        "meta": {"plan_id": "x", "generated_at": 123, "data_confidence": "bad"},
        "week": {"iso": 3, "start_date": 1, "end_date": 2},
    }
    monkeypatch.setattr(validate_week, "build_weekly_summary", lambda **_: summary)
    ok, errors, _ = validate_week.run_validate(2, "2026-W03")
    assert ok is False
    assert errors
