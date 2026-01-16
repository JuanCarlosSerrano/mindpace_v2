import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.routers import dashboard


def test_get_week_dashboard_ok(monkeypatch):
    summary = {
        "meta": {"plan_id": 2, "generated_at": "2026-01-10T00:00:00Z"},
        "week": {"iso": "2026-W03", "start_date": "2026-01-12", "end_date": "2026-01-18"},
        "plan": {"sesiones": 1, "volumen_km": 10.0, "por_tipo": {"rodaje": 1}},
        "real": {"sesiones": 1, "volumen_km": 10.0, "cobertura": 1.0},
        "comparison": {"sesiones_vinculadas": 1},
        "compliance": {"status": "OK", "label": "cumplida", "ratio_vol": 1.0, "ratio_ses": 1.0},
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
    monkeypatch.setattr(dashboard, "build_weekly_summary", lambda **_: summary)
    monkeypatch.setattr(dashboard, "validate_weekly_summary", lambda *_: None)
    client = TestClient(app)
    res = client.get("/api/v1/plans/2/weeks/2026-W03")
    assert res.status_code == 200
    assert res.json()["week"]["iso"] == "2026-W03"


def test_get_week_dashboard_contract_fail_returns_500(monkeypatch):
    summary = {"meta": {"plan_id": "x"}}
    monkeypatch.setattr(dashboard, "build_weekly_summary", lambda **_: summary)
    def _raise(*_):
        raise ValueError("bad")
    monkeypatch.setattr(dashboard, "validate_weekly_summary", _raise)
    client = TestClient(app)
    res = client.get("/api/v1/plans/2/weeks/2026-W03")
    assert res.status_code == 500
    body = res.json()
    assert body["detail"]["error"] == "WEEKLY_CONTRACT_INVALID"


def test_get_week_dashboard_invalid_week_returns_400():
    client = TestClient(app)
    res = client.get("/api/v1/plans/2/weeks/2026-W99")
    assert res.status_code == 400
    body = res.json()
    assert body["detail"]["error"] == "INVALID_ISO_WEEK"
