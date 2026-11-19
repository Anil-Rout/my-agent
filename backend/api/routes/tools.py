# tools.py - Tool discovery endpoints

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import require_authenticated_user
from api.rate_limit import limit_requests
from brain.agent import ALL_TOOLS
from database.queries import get_pending_approvals, resolve_approval


router = APIRouter(dependencies=[Depends(require_authenticated_user)])


class ToolInfo(BaseModel):
    name: str
    description: str


class CapabilityGroup(BaseModel):
    category: str
    features: list[str]


@router.get("/list", response_model=list[ToolInfo])
def list_tools(
    _: None = Depends(
        limit_requests(
            bucket="tools_list",
            env_name="RATE_LIMIT_TOOLS_PER_MINUTE",
            default_limit=60,
        )
    ),
):
    """Return the tools currently registered with the agent."""
    return [
        ToolInfo(
            name=tool.name,
            description=(tool.description or "").strip(),
        )
        for tool in ALL_TOOLS
    ]


@router.get("/capabilities", response_model=list[CapabilityGroup])
def list_capabilities(
    _: None = Depends(
        limit_requests(
            bucket="tools_capabilities",
            env_name="RATE_LIMIT_TOOLS_PER_MINUTE",
            default_limit=60,
        )
    ),
):
    """Return a grouped overview of what the local agent can do."""
    return [
        CapabilityGroup(
            category="File and Folder Control",
            features=[
                "Create folders and files",
                "Read files",
                "List desktop/documents/downloads",
                "Search files and locate folders",
                "Open specific folders and paths",
                "Delete files and folders with confirmation",
            ],
        ),
        CapabilityGroup(
            category="PC and App Control",
            features=[
                "Open desktop applications",
                "Open folders in File Explorer",
                "Show running processes",
                "Take screenshots",
                "Shutdown, restart, or cancel shutdown with confirmation",
            ],
        ),
        CapabilityGroup(
            category="System Insight",
            features=[
                "Show CPU, RAM, disk, battery, and network status",
                "Return a full system summary",
            ],
        ),
        CapabilityGroup(
            category="Browser and Search",
            features=[
                "Search the web",
                "Open Google and YouTube searches",
                "Open websites",
                "Get news and weather",
            ],
        ),
        CapabilityGroup(
            category="Code and Automation",
            features=[
                "Write Python files",
                "Run Python snippets",
                "Write and run Python code",
                "Install Python packages with confirmation",
                "Set and clear reminders",
            ],
        ),
    ]

@router.get("/approvals/{session_id}")
def list_approvals(
    session_id: str,
    _: None = Depends(require_authenticated_user),
):
    """List pending approvals for a session."""
    return {"approvals": get_pending_approvals(session_id)}


@router.post("/approvals/{approval_id}/approve")
def approve_action(
    approval_id: int,
    _: None = Depends(require_authenticated_user),
):
    resolve_approval(approval_id, "approved")
    return {"status": "approved"}


@router.post("/approvals/{approval_id}/deny")
def deny_action(
    approval_id: int,
    _: None = Depends(require_authenticated_user),
):
    resolve_approval(approval_id, "denied")
    return {"status": "denied"}
