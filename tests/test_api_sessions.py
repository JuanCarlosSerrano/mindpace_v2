import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.routers import sessions
from src.db.base import Base
from src.db.models import SessionCatalog


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
            SessionCatalog(
                name="Series 4x1000",
                description="Series largas",
                tipo_sesion="series",
                volumen_base=8.0,
                tags_json=["series", "umbral"],
            ),
            SessionCatalog(
                name="Rodaje suave",
                description="Rodaje base",
                tipo_sesion="rodaje",
                volumen_base=6.0,
                tags_json=["rodaje", "suave"],
            ),
        ]
    )
    session.commit()
    session.close()
    return SessionLocal


def test_sessions_filter_by_tipo_and_tag(monkeypatch):
    SessionLocal = _make_session_local()
    monkeypatch.setattr(sessions, "SessionLocal", SessionLocal)
    client = TestClient(app)

    res = client.get("/api/v1/sessions?tipo=series&tag=umbral")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["tipo_sesion"] == "series"


def test_session_detail_404(monkeypatch):
    SessionLocal = _make_session_local()
    monkeypatch.setattr(sessions, "SessionLocal", SessionLocal)
    client = TestClient(app)

    res = client.get("/api/v1/sessions/999")
    assert res.status_code == 404


def test_session_update_and_delete(monkeypatch):
    SessionLocal = _make_session_local()
    monkeypatch.setattr(sessions, "SessionLocal", SessionLocal)
    client = TestClient(app)

    update = client.put(
        "/api/v1/sessions/1",
        json={"name": "Series 4x1000 v2", "volumen_base": 9},
    )
    assert update.status_code == 200
    res = client.get("/api/v1/sessions/1")
    assert res.status_code == 200
    assert res.json()["name"] == "Series 4x1000 v2"

    delete = client.delete("/api/v1/sessions/1")
    assert delete.status_code == 200
    res = client.get("/api/v1/sessions/1")
    assert res.status_code == 404
