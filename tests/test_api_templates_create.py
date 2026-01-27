import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.routers import templates
from src.db.base import Base
from src.db.models import TemplateCatalog, PlantillaPlan, PlantillaSesion


def _make_session_local():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_create_template_creates_catalog_and_sessions(monkeypatch):
    SessionLocal = _make_session_local()
    monkeypatch.setattr(templates, "SessionLocal", SessionLocal)
    client = TestClient(app)

    payload = {
        "name": "Plantilla test",
        "description": "Demo",
        "goal": "base",
        "level": "base",
        "duration_weeks": 2,
        "tags": ["rodaje"],
        "sessions": [
            {"week": 1, "day_of_week": 2, "tipo_sesion": "rodaje", "volumen_base": 8},
            {"week": 2, "day_of_week": 4, "tipo_sesion": "series", "volumen_base": 6},
        ],
    }

    res = client.post("/api/v1/templates", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "id" in body

    session = SessionLocal()
    assert session.query(TemplateCatalog).count() == 1
    assert session.query(PlantillaPlan).count() == 1
    assert session.query(PlantillaSesion).count() == 2
    session.close()
