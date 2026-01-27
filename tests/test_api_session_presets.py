import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.routers import session_presets
from src.db.base import Base
from src.db.models import SessionPreset


def _make_session_local():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    session.add_all(
        [
            SessionPreset(
                entrenador_id=1,
                label="4x1000",
                tipo_sesion="series",
                volumen_base=8.0,
                formato_series="4x1000",
            ),
            SessionPreset(
                entrenador_id=2,
                label="Rodaje suave",
                tipo_sesion="rodaje",
                volumen_base=6.0,
            ),
        ]
    )
    session.commit()
    session.close()
    return SessionLocal


def test_session_presets_filter_by_trainer(monkeypatch):
    SessionLocal = _make_session_local()
    monkeypatch.setattr(session_presets, "SessionLocal", SessionLocal)
    client = TestClient(app)

    res = client.get("/api/v1/session-presets?entrenador_id=1")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["entrenador_id"] == 1


def test_session_presets_create(monkeypatch):
    SessionLocal = _make_session_local()
    monkeypatch.setattr(session_presets, "SessionLocal", SessionLocal)
    client = TestClient(app)

    res = client.post(
        "/api/v1/session-presets",
        json={
            "entrenador_id": 1,
            "label": "Tempo 20'",
            "tipo_sesion": "tempo",
            "volumen_base": 12,
        },
    )
    assert res.status_code == 200
    assert "id" in res.json()


def test_session_presets_update_and_delete(monkeypatch):
    SessionLocal = _make_session_local()
    monkeypatch.setattr(session_presets, "SessionLocal", SessionLocal)
    client = TestClient(app)

    update = client.put(
        "/api/v1/session-presets/1",
        params={"entrenador_id": 1},
        json={"label": "4x1000 v2", "volumen_base": 9},
    )
    assert update.status_code == 200

    res = client.get("/api/v1/session-presets?entrenador_id=1")
    assert res.status_code == 200
    assert res.json()["items"][0]["label"] == "4x1000 v2"

    delete = client.delete("/api/v1/session-presets/1", params={"entrenador_id": 1})
    assert delete.status_code == 200
    res = client.get("/api/v1/session-presets?entrenador_id=1")
    assert res.json()["total"] == 0
