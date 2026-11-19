# connection.py — Database connection setup

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/agent.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_database():
    """Create all tables if they don't exist"""
    os.makedirs("database", exist_ok=True)
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
