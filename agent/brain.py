# brain.py — Groq AI connection
# This is the intelligence of the agent

from groq import Groq
from dotenv import load_dotenv
from agent.prompts import get_system_prompt
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def think(user_message: str, conversation_history: list) -> str:
    """
    Send user message to Groq AI and get response.
    conversation_history keeps track of full chat so agent remembers context.
    """
    try:
        messages = [
            {"role": "system", "content": get_system_prompt()}
        ] + conversation_history + [
            {"role": "user", "content": user_message}
        ]

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            max_tokens=1024
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"
