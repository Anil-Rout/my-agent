# models.py — Database table definitions

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Message(Base):
    """Stores all chat messages"""
    __tablename__ = "messages"
    id        = Column(Integer, primary_key=True)
    role      = Column(String(20))   # user or assistant
    content   = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

class ActionLog(Base):
    """Logs every action agent takes on PC"""
    __tablename__ = "action_logs"
    id          = Column(Integer, primary_key=True)
    action_type = Column(String(50))
    description = Column(Text)
    status      = Column(String(20))  # success or failed
    timestamp   = Column(DateTime, default=datetime.now)
