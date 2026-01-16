import logging
import os

from fastapi import FastAPI
from sqlalchemy import inspect

from src.api.routers import coach, dashboard, feedback
from src.db.session import engine

app = FastAPI(title="MindPace v2 API", version="0.1")

app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(coach.router, prefix="/api/v1")

logger = logging.getLogger(__name__)


@app.on_event("startup")
def _check_db_ready() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    required = {"planes_atleta"}
    missing = required - tables
    if missing:
        app.state.db_ready = False
        app.state.db_error = f"Missing tables: {', '.join(sorted(missing))}"
        logger.warning("Database not initialized: %s", app.state.db_error)
        return
    app.state.db_ready = True
    app.state.db_error = None


@app.get("/health")
def health():
    return {"status": "ok", "db_ready": getattr(app.state, "db_ready", True)}


def main():
    import uvicorn

    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("src.api.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
