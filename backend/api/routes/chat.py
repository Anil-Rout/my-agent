import traceback
from typing import List, Optional
from tools.voice_output_tool import speak
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from api.auth import require_authenticated_user
from api.rate_limit import limit_requests
from brain.agent import AGENT_NAME, chat as run_agent_chat
from brain.memory import search_memory
from database.cache import cache_get, cache_set
from database.queries import (
    complete_task,
    create_task,
    fail_task,
    get_messages,
    get_tasks,
    list_sessions,
    save_message,
    upsert_session,
    delete_session,
)



router = APIRouter(dependencies=[Depends(require_authenticated_user)])


class HistoryMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, value: str) -> str:
        if value not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {value}")
        return value


class ChatRequest(BaseModel):
    message: str
    history: List[HistoryMessage] = Field(default_factory=list)
    agent_name: Optional[str] = None
    session_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    voice_input: bool = False  # ← add this line


class ChatResponse(BaseModel):
    response: str
    agent_name: str
    memories_used: int
    success: bool = True


def build_history(history: List[HistoryMessage]) -> list:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    messages = []
    for item in history:
        if item.role == "user":
            messages.append(HumanMessage(content=item.content))
        elif item.role == "assistant":
            messages.append(AIMessage(content=item.content))
        elif item.role == "system":
            messages.append(SystemMessage(content=item.content))
    return messages


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    raw_request: Request,
    _: None = Depends(
        limit_requests(
            bucket="chat_send",
            env_name="RATE_LIMIT_CHAT_PER_MINUTE",
            default_limit=30,
        )
    ),
):
    """
    Main chat endpoint.
    Receives message from Flutter app.
    Returns AI response with tool results.
    """
    task_id: int | None = None
    session_id = request.session_id or "default"
    user_id = getattr(raw_request.state, "user_id", "local-owner")
    agent_name = request.agent_name or AGENT_NAME

    try:
        import re
        history = build_history(request.history[-4:] if len(request.history) > 4 else request.history)

        upsert_session(
            session_id,
            user_id=user_id,
            agent_name=agent_name,
            status="running",
            last_message_preview=request.message,
        )
        save_message(session_id, "user", request.message, user_id=user_id)
        task_id = create_task(
            session_id,
            user_id=user_id,
            agent_name=agent_name,
            input_text=request.message,
        )

        _msg_lower = request.message.strip().lower()

        # ── Direct greeting handling ──
        _greetings = {
            "hlo": "Hey! What can I do for you?",
            "hi": "Hi! What do you need?",
            "hello": "Hello! How can I help?",
            "hey": "Hey! What can I do for you?",
            "how are you": "Doing great! What do you need?",
            "how r u": "Doing great! What do you need?",
            "good morning": "Good morning! What's on your mind?",
            "good evening": "Good evening! How can I help?",
            "good night": "Good night! Anything before you go?",
            "ok": "Got it!",
            "okay": "Got it!",
            "thanks": "Happy to help!",
            "thank you": "You're welcome!",
            "bye": "Goodbye! Come back anytime.",
            "what is your name": f"My name is ARIA.",
            "what's your name": f"My name is ARIA.",
            "your name": f"My name is ARIA.",
            "what is my name": None,  # handled below
            "my name": None,
            "can you please open again": "OPEN_LAST",
            "open again": "OPEN_LAST",
            "open it again": "OPEN_LAST",
            "please open again": "OPEN_LAST",
            "what can you do": "I can chat, answer questions, and control your PC — open apps, manage files, search the web, take screenshots, send WhatsApp messages, read emails, write in Notepad, and much more. Just ask!",
            "what can you do for me": "I can chat, answer questions, and control your PC — open apps, manage files, search the web, take screenshots, send WhatsApp messages, read emails, write in Notepad, and much more. Just ask!",
            "what can you do?": "I can chat, answer questions, and control your PC — open apps, manage files, search the web, take screenshots, send WhatsApp messages, read emails, write in Notepad, and much more. Just ask!",
            "what are you capable of": "I can chat, answer questions, and control your PC — open apps, manage files, search the web, take screenshots, send WhatsApp messages, read emails, write in Notepad, and much more. Just ask!",
            "help": "I can open apps, manage files, search the web, write in Notepad, send WhatsApp messages, check emails, take screenshots, and much more. What do you need?",
            "what do you do": "I can chat, answer questions, and control your PC. Just ask!",

        }


        
        # ── Direct "is X open" handling ──
        _is_open_match = re.match(
            r'^is\s+(.+?)\s+(open|running|on|active|opened)\??$',
            _msg_lower
        )

        if _is_open_match:
            app_keyword = _is_open_match.group(1).strip()
            from tools.window_tool import list_windows
            windows_result = list_windows()
            windows_data = windows_result.get("data", {}).get("windows", [])
            windows_lower = [w.lower() for w in windows_data]
            found = any(app_keyword in w for w in windows_lower)
            if found:
                response = f"Yes, {app_keyword.title()} is open."
            else:
                response = f"No, {app_keyword.title()} is not open. Want me to open it?"
            updated_name = agent_name

        elif any(p in _msg_lower for p in ["open notepad", "start notepad", "launch notepad"]):
            from tools.notepad_tool import open_notepad
            result = open_notepad()
            response = result.get("message", "Notepad is open!")
            updated_name = agent_name



        elif _msg_lower in ["new tab", "new notepad tab", "open new tab", "create new tab"]:
            from tools.notepad_tool import new_tab
            result = new_tab()
            response = result.get("message", "New tab created in Notepad.")
            updated_name = agent_name

        elif _msg_lower in ["save", "save it", "save this", "save the file", "save notepad"]:
            from tools.notepad_tool import save_file
            result = save_file()
            response = result.get("message", "File saved.")
            updated_name = agent_name

        elif _msg_lower in ["clear notepad", "clear it", "clear the notepad", "delete all", "clear all"]:
            from tools.notepad_tool import clear_notepad
            result = clear_notepad()
            response = result.get("message", "Notepad cleared.")
            updated_name = agent_name

        elif _msg_lower in ["undo", "undo that", "undo last"]:
            from tools.notepad_tool import undo
            result = undo()
            response = result.get("message", "Undo applied.")
            updated_name = agent_name

        elif _msg_lower in ["redo", "redo that"]:
            from tools.notepad_tool import redo
            result = redo()
            response = result.get("message", "Redo applied.")
            updated_name = agent_name

            
        elif _msg_lower in _greetings:
            response = _greetings[_msg_lower]
            updated_name = agent_name


        elif "what is my name" in _msg_lower or "my name" == _msg_lower:
            from tools.learning_system import _load
            store = _load()
            name = store.get("user_profile", {}).get("name")
            if name:
                response = f"Your name is {name}."
            else:
                response = "I don't know your name yet. Tell me and I'll remember it!"
            updated_name = agent_name


        elif _greetings.get(_msg_lower) == "OPEN_LAST" or "open again" in _msg_lower:
            response = "Sure! What would you like me to open?"
            updated_name = agent_name


        elif _msg_lower in ["what is my name", "what's my name", "my name", "do you know my name"]:
            from tools.learning_system import _load
            store = _load()
            name = store.get("user_profile", {}).get("name")
            response = f"Your name is {name}." if name else "I don't know your name yet — tell me!"
            updated_name = agent_name

        elif any(p in _msg_lower for p in ["start writing", "write in notepad", "type in notepad", "write this in notepad"]):
            # Extract what to write
            text_to_write = request.message
            for prefix in ["start writing -", "start writing:", "start writing", 
                          "write in notepad -", "write in notepad:", "write in notepad",
                          "type in notepad -", "type in notepad:", "type in notepad",
                          "write this in notepad -", "write this in notepad:", "write this in notepad"]:
                if text_to_write.lower().startswith(prefix.lower()):
                    text_to_write = text_to_write[len(prefix):].strip().strip("-").strip()
                    break
            if text_to_write:
                from tools.notepad_tool import write_text
                result = write_text(text_to_write)
                response = result.get("message", f"Written in Notepad: {text_to_write}")
            else:
                response = "What would you like me to write?"
            updated_name = agent_name

        else:
            response, updated_name = run_agent_chat(
                request.message,
                history,
                agent_name,
                session_id=session_id,
            )

        if not response or not response.strip():
            response = "Got it! What else can I do for you?"

        # Speak response if voice input
        if request.voice_input:
            from tools.voice_output_tool import speak
            speak(response)

        save_message(session_id, "assistant", response, user_id=user_id)
        upsert_session(
            session_id,
            user_id=user_id,
            agent_name=updated_name,
            status="active",
            last_message_preview=response,
        )
        complete_task(task_id, response)

        from tools.learning_system import process_message
        process_message(request.message, response, session_id=session_id)

        memories = search_memory(request.message, top_k=2)

        return ChatResponse(
            response=response,
            agent_name=updated_name,
            memories_used=len(memories),
            success=True,
        )
    
    except Exception as exc:
        fail_task(task_id, str(exc))
        upsert_session(
            session_id,
            user_id=user_id,
            agent_name=agent_name,
            status="error",
            last_message_preview=request.message,
        )
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Agent execution failed. Please try again in a moment.",
        ) from None


@router.get("/history")
async def get_history(
    session_id: str = "default",
    limit: int = 20,
    _: None = Depends(
        limit_requests(
            bucket="chat_history",
            env_name="RATE_LIMIT_CHAT_PER_MINUTE",
            default_limit=30,
        )
    ),
):
    """Get recent conversation history from the database."""
    try:
        history = get_messages(session_id, limit=limit)
        return {"history": history, "count": len(history), "session_id": session_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tasks")
async def get_task_history(
    session_id: str | None = None,
    limit: int = 20,
    _: None = Depends(
        limit_requests(
            bucket="chat_tasks",
            env_name="RATE_LIMIT_CHAT_PER_MINUTE",
            default_limit=30,
        )
    ),
):
    """Get recent durable task records."""
    try:
        tasks = get_tasks(session_id=session_id, limit=limit)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions")
async def get_sessions(
    limit: int = 20,
    _: None = Depends(
        limit_requests(
            bucket="chat_sessions",
            env_name="RATE_LIMIT_CHAT_PER_MINUTE",
            default_limit=30,
        )
    ),
):
    """List recent durable sessions."""
    try:
        sessions = list_sessions(limit=limit)
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/sessions/{session_id}")
async def remove_session(
    session_id: str,
    _: None = Depends(
        limit_requests(
            bucket="chat_sessions",
            env_name="RATE_LIMIT_CHAT_PER_MINUTE",
            default_limit=30,
        )
    ),
):
    """Delete a session and all its messages."""
    try:
        success = delete_session(session_id)
        if success:
            return {"success": True, "message": f"Session {session_id} deleted."}
        raise HTTPException(status_code=500, detail="Failed to delete session.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc