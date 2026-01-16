import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.routers import coach


class _Rec:
    def __init__(self):
        self.tipo = "semanal"
        self.resumen = "Ajuste de carga semanal"
        self.acciones = ["Semana marcada como descarga"]
        self.explicacion = "x"
        self.semana = "2026-W03"
        self.fecha = None
        self.scope = "weekly"
        self.reason = "LOW"
        self.confidence = "medium"
        self.kind = "adjustment"
        self.severity = "medium"
        self.priority = 3


def test_post_coach_apply_dry_run_ok(monkeypatch):
    class _Coach:
        def proponer_ajustes(self, *_):
            return [_Rec()]

    monkeypatch.setattr(coach, "CoachAI", _Coach)
    client = TestClient(app)
    res = client.post(
        "/api/v1/plans/2/coach/apply",
        json={"week": "2026-W03", "dry_run": True},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["dry_run"] is True
    assert body["recommendations"]
