from datetime import datetime

from database.connection import SessionLocal
from database.models import (
    ActionLog,
    AgentState,
    Approval,
    Message,
    SessionRecord,
    TaskRecord,
    TaskStep,
)
import json


def delete_session(session_id: str) -> bool:
    """Delete a session and all its messages and tasks."""
    db = SessionLocal()
    try:
        db.query(Message).filter(Message.session_id == session_id).delete()
        db.query(TaskRecord).filter(TaskRecord.session_id == session_id).delete()
        db.query(SessionRecord).filter(SessionRecord.session_id == session_id).delete()
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        print(f"DB delete_session error: {exc}")
        return False
    finally:
        db.close()

        
def create_approval(
    session_id: str,
    tool_name: str,
    tool_args: dict,
    *,
    user_id: str = "local-owner",
    task_id: int | None = None,
    reason: str = "",
) -> int | None:
    db = SessionLocal()
    try:
        record = Approval(
            task_id=task_id,
            session_id=session_id,
            user_id=user_id,
            tool_name=tool_name,
            tool_args_json=json.dumps(tool_args),
            reason=reason,
            status="pending",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.id
    except Exception as exc:
        db.rollback()
        print(f"DB create_approval error: {exc}")
        return None
    finally:
        db.close()


def resolve_approval(approval_id: int, status: str) -> None:
    """status = 'approved' or 'denied'"""
    db = SessionLocal()
    try:
        record = db.query(Approval).filter(Approval.id == approval_id).first()
        if record:
            record.status = status
            record.resolved_at = datetime.now()
            db.commit()
    except Exception as exc:
        db.rollback()
        print(f"DB resolve_approval error: {exc}")
    finally:
        db.close()


def get_pending_approvals(session_id: str) -> list[dict]:
    db = SessionLocal()
    try:
        records = (
            db.query(Approval)
            .filter(
                Approval.session_id == session_id,
                Approval.status == "pending",
            )
            .all()
        )
        return [
            {
                "id": r.id,
                "tool_name": r.tool_name,
                "tool_args": json.loads(r.tool_args_json),
                "reason": r.reason,
                "requested_at": r.requested_at.isoformat(),
            }
            for r in records
        ]
    finally:
        db.close()


def create_task_step(
    task_id: int,
    session_id: str,
    step_index: int,
    tool_name: str,
    tool_args: dict,
    output_text: str = "",
    error_text: str = "",
    success: bool = True,
) -> None:
    db = SessionLocal()
    try:
        db.add(TaskStep(
            task_id=task_id,
            session_id=session_id,
            step_index=step_index,
            tool_name=tool_name,
            tool_args=json.dumps(tool_args),
            output_text=output_text[:2000],
            error_text=error_text[:1000],
            success=success,
        ))
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"DB create_task_step error: {exc}")
    finally:
        db.close()

def save_message(
    session_id: str,
    role: str,
    content: str,
    user_id: str = "local-owner",
) -> None:
    """Save a chat message to the database."""
    db = SessionLocal()
    try:
        db.add(
            Message(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                timestamp=datetime.now(),
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"DB save_message error: {exc}")
    finally:
        db.close()


def get_messages(session_id: str, limit: int = 20) -> list[dict]:
    """Get recent messages for a session."""
    db = SessionLocal()
    try:
        msgs = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "user_id": msg.user_id,
            }
            for msg in reversed(msgs)
        ]
    finally:
        db.close()


def upsert_session(
    session_id: str,
    *,
    user_id: str = "local-owner",
    agent_name: str = "My Agent",
    status: str = "active",
    last_message_preview: str = "",
) -> None:
    """Create or update a durable session record."""
    db = SessionLocal()
    try:
        session = (
            db.query(SessionRecord)
            .filter(SessionRecord.session_id == session_id)
            .first()
        )
        preview = last_message_preview[:240] if last_message_preview else ""

        if session:
            session.user_id = user_id
            session.agent_name = agent_name
            session.status = status
            session.last_message_preview = preview
            session.updated_at = datetime.now()
        else:
            db.add(
                SessionRecord(
                    session_id=session_id,
                    user_id=user_id,
                    agent_name=agent_name,
                    status=status,
                    last_message_preview=preview,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            )
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"DB upsert_session error: {exc}")
    finally:
        db.close()


def list_sessions(limit: int = 20) -> list[dict]:
    """List recent durable session records."""
    db = SessionLocal()
    try:
        sessions = (
            db.query(SessionRecord)
            .order_by(SessionRecord.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "session_id": item.session_id,
                "user_id": item.user_id,
                "agent_name": item.agent_name,
                "status": item.status,
                "last_message_preview": item.last_message_preview,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }
            for item in sessions
        ]
    finally:
        db.close()


def create_task(
    session_id: str,
    *,
    user_id: str = "local-owner",
    agent_name: str = "My Agent",
    task_type: str = "chat",
    input_text: str,
) -> int | None:
    """Create a durable task record and return its id."""
    db = SessionLocal()
    try:
        task = TaskRecord(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            task_type=task_type,
            input_text=input_text,
            status="running",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task.id
    except Exception as exc:
        db.rollback()
        print(f"DB create_task error: {exc}")
        return None
    finally:
        db.close()


def complete_task(task_id: int | None, response_text: str) -> None:
    """Mark a task as completed."""
    if task_id is None:
        return

    db = SessionLocal()
    try:
        task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
        if not task:
            return
        task.status = "completed"
        task.response_text = response_text[:4000] if response_text else ""
        task.error_text = ""
        task.updated_at = datetime.now()
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"DB complete_task error: {exc}")
    finally:
        db.close()


def fail_task(task_id: int | None, error_text: str) -> None:
    """Mark a task as failed."""
    if task_id is None:
        return

    db = SessionLocal()
    try:
        task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
        if not task:
            return
        task.status = "failed"
        task.error_text = error_text[:4000] if error_text else ""
        task.updated_at = datetime.now()
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"DB fail_task error: {exc}")
    finally:
        db.close()


def get_tasks(session_id: str | None = None, limit: int = 20) -> list[dict]:
    """Return recent durable tasks, optionally filtered by session."""
    db = SessionLocal()
    try:
        query = db.query(TaskRecord)
        if session_id:
            query = query.filter(TaskRecord.session_id == session_id)
        tasks = query.order_by(TaskRecord.created_at.desc()).limit(limit).all()
        return [
            {
                "id": task.id,
                "session_id": task.session_id,
                "user_id": task.user_id,
                "agent_name": task.agent_name,
                "task_type": task.task_type,
                "input_text": task.input_text,
                "status": task.status,
                "response_text": task.response_text,
                "error_text": task.error_text,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
            for task in tasks
        ]
    finally:
        db.close()


def log_action(
    session_id: str,
    action_type: str,
    tool_name: str,
    description: str,
    result: str,
    success: bool,
) -> None:
    """Log an agent action to the database."""
    db = SessionLocal()
    try:
        db.add(
            ActionLog(
                session_id=session_id,
                action_type=action_type,
                tool_name=tool_name,
                description=description,
                result=result[:500] if result else "",
                success=success,
                timestamp=datetime.now(),
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"DB log_action error: {exc}")
    finally:
        db.close()


def get_agent_state(key: str) -> str | None:
    """Get a persistent agent state value."""
    db = SessionLocal()
    try:
        state = db.query(AgentState).filter(AgentState.key == key).first()
        return state.value if state else None
    finally:
        db.close()


def set_agent_state(key: str, value: str) -> None:
    """Set a persistent agent state value."""
    db = SessionLocal()
    try:
        state = db.query(AgentState).filter(AgentState.key == key).first()
        if state:
            state.value = value
            state.updated_at = datetime.now()
        else:
            db.add(AgentState(key=key, value=value))
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"DB set_agent_state error: {exc}")
    finally:
        db.close()
