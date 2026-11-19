# Chat routes - handles all chat messages
from fastapi import APIRouter
from pydantic import BaseModel
from agent.brain import think
from agent.memory import add_message, get_messages_for_ai, clear_memory
from server.routes.actions import execute_action
import re

router = APIRouter()

class Message(BaseModel):
    content: str

@router.post("/send")
def send_message(message: Message):
    # Save user message
    add_message("user", message.content)
    
    # Get AI response
    messages = get_messages_for_ai()
    response = think(messages)
    
    # Check if AI wants to execute an action
    action_result = None
    if "ACTION:" in response:
        action_result = execute_action(response)
        if action_result:
            response = response + f"\n\nResult: {action_result}"
    
    # Save agent response
    add_message("assistant", response)
    
    return {"response": response, "action_result": action_result}

@router.get("/history")
def get_history():
    from agent.memory import load_memory
    return {"messages": load_memory()}

@router.delete("/clear")
def clear_chat():
    clear_memory()
    return {"status": "Chat cleared"}
