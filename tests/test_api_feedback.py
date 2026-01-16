import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
from fastapi.testclient import TestClient

from datetime import date
from src.api.app import app

from src.api.routers import feedback


class _Feedback:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_post_feedback_upsert_ok(monkeypatch):
    feedback_obj = _Feedback(
        id=1,
        athlete_id=1,
        plan_id=2,
        session_date=date(2026, 1, 15),
        rpe=8,
        mood=4,
        fatigue=7,
        soreness=3,
        pain_flag=False,
        notes="Piernas cargadas",
        created_at=date(2026, 1, 15),
        updated_at=date(2026, 1, 15),
    )

    monkeypatch.setattr(
        feedback,
        "upsert_feedback",
        lambda **_: feedback_obj,
    )
    client = TestClient(app)
    res = client.post(
        "/api/v1/athletes/1/feedback",
        json={
            "date": "2026-01-15",
            "plan_id": 2,
            "rpe": 8,
            "fatigue": 7,
            "soreness": 3,
            "pain": False,
            "notes": "Piernas cargadas",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == 1
    assert body["athlete_id"] == 1
