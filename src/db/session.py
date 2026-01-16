import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = os.getenv("DB_PATH", "mindpace_dev.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)
