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
from src.db.models import TemplateCatalog


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
            TemplateCatalog(
                name="Base 8 semanas",
                description="Base aeróbica",
                goal="base",
                level="intermedio",
                duration_weeks=8,
                tags_json=["rodaje", "base"],
                estimated_weekly_load=42.0,
            ),
            TemplateCatalog(
                name="10K rápido",
                description="Series y umbral",
                goal="10k",
                level="avanzado",
                duration_weeks=12,
                tags_json=["series", "umbral"],
                estimated_weekly_load=58.0,
            ),
        ]
    )
    session.commit()
    session.close()
    return SessionLocal


def test_templates_filter_by_goal_and_tag(monkeypatch):
    SessionLocal = _make_session_local()
    monkeypatch.setattr(templates, "SessionLocal", SessionLocal)
    client = TestClient(app)

    res = client.get("/api/v1/templates?goal=base&tag=rodaje")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["goal"] == "base"


def test_template_detail_404(monkeypatch):
    SessionLocal = _make_session_local()
    monkeypatch.setattr(templates, "SessionLocal", SessionLocal)
    client = TestClient(app)

    res = client.get("/api/v1/templates/999")
    assert res.status_code == 404
