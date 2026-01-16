from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.feedback.repo import upsert_feedback

DB_PATH = os.getenv("DB_PATH", "mindpace_dev.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    date: date
    plan_id: int | None = None
    rpe: int | None = Field(default=None, ge=1, le=10)
    mood: int | None = Field(default=None, ge=1, le=5)
    fatigue: int | None = Field(default=None, ge=1, le=10)
    soreness: int | None = Field(default=None, ge=1, le=10)
    pain: bool | None = None
    notes: str | None = None


@router.post("/athletes/{athlete_id}/feedback")
def post_feedback(athlete_id: int, payload: FeedbackRequest):
    session = Session()
    data = payload.model_dump()
    pain = data.pop("pain", None)
    if pain is not None:
        data["pain_flag"] = pain
    feedback = upsert_feedback(
        session=session,
        athlete_id=athlete_id,
        plan_id=data.pop("plan_id", None),
        session_date=data.pop("date"),
        payload=data,
    )
    return {
        "id": feedback.id,
        "athlete_id": feedback.athlete_id,
        "plan_id": feedback.plan_id,
        "date": feedback.session_date.isoformat(),
        "rpe": feedback.rpe,
        "mood": feedback.mood,
        "fatigue": feedback.fatigue,
        "soreness": feedback.soreness,
        "pain_flag": feedback.pain_flag,
        "notes": feedback.notes,
        "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
        "updated_at": feedback.updated_at.isoformat() if feedback.updated_at else None,
    }
