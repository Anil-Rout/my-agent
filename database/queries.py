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