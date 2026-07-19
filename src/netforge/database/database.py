from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'netforge.db'}"

engine = create_engine(
    DATABASE_URL,
    echo=False
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

from netforge.database.base import Base
from netforge.models.connection import Connection

def initialize_database():
    Base.metadata.create_all(bind=engine)