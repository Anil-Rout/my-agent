# system.py - System information endpoints

from fastapi import APIRouter, Depends, HTTPException

from api.auth import require_authenticated_user
from api.rate_limit import limit_requests
from security.audit_log import get_action_summary, get_recent_actions
from tools.system_tool import get_system_summary


router = APIRouter(dependencies=[Depends(require_authenticated_user)])


@router.get("/info")
def system_info(
    _: None = Depends(
        limit_requests(
            bucket="system_info",
            env_name="RATE_LIMIT_SYSTEM_PER_MINUTE",
            default_limit=60,
        )
    ),
):
    """Get complete PC system information."""
    try:
        result = get_system_summary()
        return {
            "success": result.get("success", True),
            "summary": result.get("data", {}).get("summary", ""),
            "message": result.get("message", ""),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/activity")
def system_activity(
    limit: int = 20,
    _: None = Depends(
        limit_requests(
            bucket="system_activity",
            env_name="RATE_LIMIT_SYSTEM_PER_MINUTE",
            default_limit=60,
        )
    ),
):
    """Get recent agent activity log."""
    try:
        actions = get_recent_actions(limit)
        return {"activity": actions, "count": len(actions)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/summary")
def activity_summary(
    _: None = Depends(
        limit_requests(
            bucket="system_summary",
            env_name="RATE_LIMIT_SYSTEM_PER_MINUTE",
            default_limit=60,
        )
    ),
):
    """Get activity summary."""
    try:
        return {"summary": get_action_summary()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
