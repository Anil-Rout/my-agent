from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Message(Base):
    """Stores all chat messages."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), index=True)
    user_id = Column(String(100), index=True, default="local-owner")
    role = Column(String(20))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)


class ActionLog(Base):
    """Logs every action agent takes on PC."""

    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), index=True)
    action_type = Column(String(50))
    tool_name = Column(String(100))
    description = Column(Text)
    result = Column(Text)
    success = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.now)


class AgentState(Base):
    """Stores persistent agent state."""

    __tablename__ = "agent_state"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.now)


class SessionRecord(Base):
    """Durable state for a chat/control session."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, index=True)
    user_id = Column(String(100), index=True, default="local-owner")
    agent_name = Column(String(100), default="My Agent")
    status = Column(String(50), default="active")
    last_message_preview = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class TaskRecord(Base):
    """Tracks user requests as durable tasks."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), index=True)
    user_id = Column(String(100), index=True, default="local-owner")
    agent_name = Column(String(100), default="My Agent")
    task_type = Column(String(50), default="chat")
    input_text = Column(Text)
    status = Column(String(50), default="running")
    response_text = Column(Text, default="")
    error_text = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)



class TaskStep(Base):
    """Tracks individual steps inside a task."""
    __tablename__ = "task_steps"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, index=True)
    session_id = Column(String(100), index=True)
    step_index = Column(Integer, default=0)
    tool_name = Column(String(100))
    tool_args = Column(Text, default="")
    output_text = Column(Text, default="")
    error_text = Column(Text, default="")
    success = Column(Boolean, default=True)
    attempt_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)


class Approval(Base):
    """Persistent confirmation/approval records for dangerous tools."""
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, index=True, nullable=True)
    session_id = Column(String(100), index=True)
    user_id = Column(String(100), default="local-owner")
    tool_name = Column(String(100))
    tool_args_json = Column(Text, default="{}")
    reason = Column(Text, default="")
    # status: pending | approved | denied | expired
    status = Column(String(20), default="pending")
    requested_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime, nullable=True)